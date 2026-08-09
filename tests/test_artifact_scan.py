import io
import json
import tarfile
import zipfile
from pathlib import Path

import pytest

from cy16boot.artifact_scan import (
    SCHEMA_ID,
    ScanError,
    scan_roots,
    write_report,
)


def matches_for(report, *, location=None, container=None, fingerprint=None):
    result = report["matches"]
    if location is not None:
        result = [item for item in result if item["location"] == location]
    if container is not None:
        result = [item for item in result if item["container"] == container]
    if fingerprint is not None:
        result = [item for item in result if item["fingerprint"] == fingerprint]
    return result


def test_regular_file_name_path_and_content_fingerprints(tmp_path):
    target = tmp_path / "Cypress" / "USB" / "OTG-Host" / "Common" / "ISRS.S"
    target.parent.mkdir(parents=True)
    target.write_text(
        "COMM_CTRL_REG_ADDR equ 01BAh\nHUSB_SIE1_INIT_INT equ 0072h\n",
        encoding="ascii",
    )

    report = scan_roots([tmp_path], content_scan=True)
    assert report["schema"] == SCHEMA_ID
    assert report["summary"]["files_scanned"] == 1
    assert report["summary"]["matches"] >= 4
    assert matches_for(report, fingerprint="ISRS.S")
    assert matches_for(report, fingerprint="Cypress/USB/OTG-Host")
    assert matches_for(report, fingerprint="Common/ISRS.S")
    assert matches_for(report, fingerprint="COMM_CTRL_REG_ADDR")
    assert matches_for(report, fingerprint="HUSB_SIE1_INIT_INT")
    for item in report["matches"]:
        assert len(item["sha256"]) == 64
        assert item["container"] is None
        assert item["kind"] == "file"


def test_content_scan_is_opt_in(tmp_path):
    source = tmp_path / "otherwise-uninteresting.txt"
    source.write_text("COMM_WRITE_CTRL_REG\n", encoding="ascii")

    without = scan_roots([tmp_path], content_scan=False)
    with_content = scan_roots([tmp_path], content_scan=True)
    assert without["summary"]["matches"] == 0
    assert matches_for(with_content, fingerprint="COMM_WRITE_CTRL_REG")


def test_content_limit_prevents_large_file_scan(tmp_path):
    source = tmp_path / "large.bin"
    source.write_bytes(b"COMM_LAST_DATA" + b"x" * 1024)
    report = scan_roots([tmp_path], content_scan=True, content_max_bytes=8)
    assert report["summary"]["matches"] == 0


def test_zip_members_are_inventoried_without_extraction(tmp_path):
    archive_path = tmp_path / "course-media.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "Source/coprocessor/linux/drivers/usb/cy7c67300/usbd/dedev/de1_bios.asm",
            "HUSB_RESET_INT\n",
        )
        archive.writestr("safe/notes.txt", "nothing relevant\n")
        archive.writestr("../unsafe/ISRS.S", "COMM_LAST_DATA\n")

    report = scan_roots([tmp_path], inspect_archives=True, content_scan=True)
    assert report["summary"]["archives_inspected"] == 1
    member_hits = [item for item in report["matches"] if item["kind"] == "zip-member"]
    assert member_hits
    assert any(item["container"] == "course-media.zip" for item in member_hits)
    assert any(item["fingerprint"] == "de1_bios.asm" for item in member_hits)
    assert any(item["fingerprint"] == "HUSB_RESET_INT" for item in member_hits)
    assert any(item["location"].startswith("UNSAFE:") for item in member_hits)
    assert not (tmp_path.parent / "unsafe").exists()


def test_tar_members_are_inventoried_without_extraction(tmp_path):
    archive_path = tmp_path / "old-install.tar.gz"
    payload = b"DEFAULT_EOT MAX_FRAME_BW\n"
    with tarfile.open(archive_path, "w:gz") as archive:
        info = tarfile.TarInfo("Source/coprocessor/de_app/cy7c67200_300_hcd.c")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))

    report = scan_roots([tmp_path], inspect_archives=True, content_scan=True)
    hits = [item for item in report["matches"] if item["kind"] == "tar-member"]
    assert any(item["fingerprint"] == "cy7c67200_300_hcd.c" for item in hits)
    assert any(item["fingerprint"] == "Source/coprocessor/de_app" for item in hits)
    assert any(item["fingerprint"] == "DEFAULT_EOT" for item in hits)
    assert any(item["fingerprint"] == "MAX_FRAME_BW" for item in hits)


def test_archive_inspection_can_be_disabled(tmp_path):
    archive_path = tmp_path / "unrelated.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("Common/ISRS.S", "COMM_CTRL_REG_DATA\n")
    report = scan_roots([tmp_path], inspect_archives=False, content_scan=True)
    assert report["summary"]["archives_inspected"] == 0
    assert not [item for item in report["matches"] if item["container"]]


def test_report_is_deterministic_for_same_tree(tmp_path):
    (tmp_path / "b").mkdir()
    (tmp_path / "a").mkdir()
    (tmp_path / "b" / "scanwrap.c").write_text("cy16-elf-objcopy\n")
    (tmp_path / "a" / "BAL.ld").write_text("SECTIONS {}\n")

    first = scan_roots([tmp_path], content_scan=True)
    second = scan_roots([tmp_path], content_scan=True)
    assert first == second

    output = tmp_path / "report.json"
    write_report(output, first)
    encoded = output.read_bytes()
    assert encoded.endswith(b"\n")
    assert json.loads(encoded) == first


def test_missing_root_and_negative_content_limit_are_rejected(tmp_path):
    with pytest.raises(ScanError, match="does not exist"):
        scan_roots([tmp_path / "missing"])
    with pytest.raises(ScanError, match="non-negative"):
        scan_roots([tmp_path], content_max_bytes=-1)


def test_single_file_root_uses_parent_as_relative_base(tmp_path):
    source = tmp_path / "ml40x_usb.zip"
    source.write_bytes(b"not actually a zip")
    report = scan_roots([source], inspect_archives=True)
    hits = matches_for(report, location="ml40x_usb.zip", fingerprint="ml40x_usb.zip")
    assert hits
    assert hits[0]["container"] is None
    assert hits[0]["sha256"]


def test_duplicate_name_and_content_hits_are_deduplicated(tmp_path):
    source = tmp_path / "scanwrap.c"
    source.write_text("scanwrap.c\nscanwrap.c\n", encoding="ascii")
    report = scan_roots([tmp_path], content_scan=True)
    name_hits = [
        item
        for item in report["matches"]
        if item["location"] == "scanwrap.c"
        and item["fingerprint_class"] == "file_name"
        and item["fingerprint"] == "scanwrap.c"
    ]
    assert len(name_hits) == 1
