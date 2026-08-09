from __future__ import annotations

import io
import os
import tarfile
import zipfile
from pathlib import Path

import pytest

from cy16boot.artifact_scan import ScanError, scan_roots


def make_symlink(link: Path, target: Path, *, directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")


def test_directory_scan_skips_file_symlink_without_resolving_target(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    secret = outside / "ISRS.S"
    secret.write_text("COMM_CTRL_REG_ADDR\n", encoding="ascii")
    link = root / "linked-secret.s"
    make_symlink(link, secret)

    report = scan_roots([root], content_scan=True)

    assert report["summary"]["files_scanned"] == 0
    assert report["summary"]["matches"] == 0
    assert report["summary"]["errors"] == 1
    assert report["errors"] == [
        {"path": "linked-secret.s", "error": "filesystem symlink skipped"}
    ]
    encoded = str(report)
    assert str(secret.resolve()) not in encoded
    assert str(outside.resolve()) not in encoded


def test_directory_scan_does_not_traverse_symlinked_directory(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "BAL.ld").write_text("SECTIONS {}\n", encoding="ascii")
    (outside / "ISRS.S").write_text("COMM_CTRL_REG_DATA\n", encoding="ascii")
    linked_dir = root / "linked-dir"
    make_symlink(linked_dir, outside, directory=True)

    report = scan_roots([root], content_scan=True)

    assert report["summary"]["files_scanned"] == 1
    assert any(item["fingerprint"] == "BAL.ld" for item in report["matches"])
    assert not any(item["fingerprint"] == "ISRS.S" for item in report["matches"])
    assert {"path": "linked-dir", "error": "filesystem symlink skipped"} in report["errors"]
    assert str(outside.resolve()) not in str(report)


def test_symlink_root_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    root_link = tmp_path / "root-link"
    make_symlink(root_link, target, directory=True)

    with pytest.raises(ScanError, match="root must not be a symlink"):
        scan_roots([root_link])


def make_zip(path: Path, members: list[tuple[str, bytes]]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members:
            archive.writestr(name, data)


def make_tar(path: Path, members: list[tuple[str, bytes]]) -> None:
    with tarfile.open(path, "w:gz") as archive:
        for name, data in members:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


@pytest.mark.parametrize("kind", ["zip", "tar"])
def test_archive_member_count_limit_is_visible_and_deterministic(
    tmp_path: Path,
    kind: str,
) -> None:
    members = [
        ("a/ISRS.S", b"COMM_CTRL_REG_ADDR\n"),
        ("b/BAL.ld", b"SECTIONS {}\n"),
        ("c/scanwrap.c", b"cy16-elf-objcopy\n"),
    ]
    if kind == "zip":
        archive = tmp_path / "many.zip"
        make_zip(archive, members)
    else:
        archive = tmp_path / "many.tar.gz"
        make_tar(archive, members)

    first = scan_roots(
        [tmp_path],
        content_scan=True,
        archive_max_members=2,
    )
    second = scan_roots(
        [tmp_path],
        content_scan=True,
        archive_max_members=2,
    )

    assert first == second
    assert first["summary"]["archives_inspected"] == 1
    assert first["summary"]["archives_incomplete"] == 1
    assert first["summary"]["errors"] == 1
    assert "member-count limit 2 reached" in first["errors"][0]["error"]
    assert any(item["fingerprint"] == "ISRS.S" for item in first["matches"])
    assert any(item["fingerprint"] == "BAL.ld" for item in first["matches"])
    assert not any(item["fingerprint"] == "scanwrap.c" for item in first["matches"])


@pytest.mark.parametrize("kind", ["zip", "tar"])
def test_archive_cumulative_read_limit_preserves_prior_matches(
    tmp_path: Path,
    kind: str,
) -> None:
    members = [
        ("a.txt", b"CY3663"),
        ("b.txt", b"CY4640"),
    ]
    if kind == "zip":
        archive = tmp_path / "budget.zip"
        make_zip(archive, members)
    else:
        archive = tmp_path / "budget.tar.gz"
        make_tar(archive, members)

    report = scan_roots(
        [tmp_path],
        content_scan=True,
        archive_max_read_bytes=6,
    )

    assert report["summary"]["archives_incomplete"] == 1
    assert "cumulative-content-bytes limit 6 reached" in report["errors"][0]["error"]
    assert any(item["fingerprint"] == "CY3663" for item in report["matches"])
    assert not any(item["fingerprint"] == "CY4640" for item in report["matches"])


def test_zero_read_budget_still_allows_name_only_inventory(tmp_path: Path) -> None:
    archive = tmp_path / "names.zip"
    make_zip(archive, [("Common/ISRS.S", b"COMM_CTRL_REG_ADDR\n")])

    report = scan_roots(
        [tmp_path],
        content_scan=False,
        archive_max_read_bytes=0,
    )

    # The matching name is visible, but hashing it would require reading bytes,
    # so the archive is explicitly incomplete rather than silently truncated.
    assert report["summary"]["archives_incomplete"] == 1
    assert not [item for item in report["matches"] if item["container"]]
    assert "cumulative-content-bytes limit 0 reached" in report["errors"][0]["error"]


def test_negative_archive_limits_are_rejected(tmp_path: Path) -> None:
    for keyword in ("archive_max_members", "archive_max_read_bytes"):
        with pytest.raises(ScanError, match=f"{keyword} must be non-negative"):
            scan_roots([tmp_path], **{keyword: -1})


def test_report_records_budget_configuration(tmp_path: Path) -> None:
    (tmp_path / "BAL.ld").write_text("SECTIONS {}\n", encoding="ascii")
    report = scan_roots(
        [tmp_path],
        archive_max_members=123,
        archive_max_read_bytes=456,
    )
    assert report["scanner"]["follow_symlinks"] is False
    assert report["scanner"]["archive_max_members"] == 123
    assert report["scanner"]["archive_max_read_bytes"] == 456
    assert report["summary"]["archives_incomplete"] == 0
