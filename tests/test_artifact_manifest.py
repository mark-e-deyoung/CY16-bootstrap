import copy
import hashlib
import json
from pathlib import Path

import pytest

from cy16boot.artifact_manifest import (
    ManifestError,
    build_manifest,
    validate_manifest_data,
    validate_manifest_file,
    write_manifest,
)
from cy16boot.asm import assemble
from cy16boot.scan import (
    SCAN_OP_CALL,
    SCAN_OP_COPY,
    make_config_record,
    make_record,
    wrap_payload,
)

SETUP_SOURCE = """
.org 0x1000
_start:
    mov [0xc03a], 0x23b3
    ret
"""
PRODUCER_COMMIT = "1" * 40


def make_artifact(tmp_path: Path):
    raw, _, _ = assemble(SETUP_SOURCE, base=0x1000)
    scan = wrap_payload(raw, 0x1000)
    raw_path = tmp_path / "setup_stub.bin"
    scan_path = tmp_path / "setup_stub.scan"
    manifest_path = tmp_path / "setup_stub.manifest.json"
    raw_path.write_bytes(raw)
    scan_path.write_bytes(scan)
    manifest = build_manifest(
        raw_path,
        scan_path,
        manifest_path,
        load_address=0x1000,
        entry_point=0x1000,
        execution_model="bios-cooperative",
        target_device="CY7C67200",
        producer_repository="mark-e-deyoung/CY16-bootstrap",
        producer_commit=PRODUCER_COMMIT,
        tool_version="0.1.0-test",
        constraints=["Requires BIOS LCP CALL support."],
        provenance_notes=["Clean-room setup-stub validation fixture."],
    )
    write_manifest(manifest_path, manifest)
    return raw_path, scan_path, manifest_path, manifest


def test_schema_is_valid_json_and_versioned():
    schema = json.loads(
        Path("spec/cy16-scan-artifact-v1.schema.json").read_text(encoding="utf-8")
    )
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"]["const"] == 1
    assert schema["additionalProperties"] is False


def test_build_and_validate_canonical_setup_stub(tmp_path):
    raw_path, scan_path, manifest_path, manifest = make_artifact(tmp_path)
    validated = validate_manifest_file(manifest_path)

    assert validated == manifest
    assert manifest["schema"] == "cy16-scan-artifact/v1"
    assert manifest["schema_version"] == 1
    assert manifest["target"] == {"family": "C67x00", "device": "CY7C67200"}
    assert manifest["image"]["load_address"] == 0x1000
    assert manifest["image"]["entry_point"] == 0x1000
    assert manifest["image"]["raw_binary"]["path"] == raw_path.name
    assert manifest["image"]["scan"]["path"] == scan_path.name
    assert manifest["image"]["raw_binary"]["sha256"] == (
        "fe76c3f54ae4d60c0cfa95df2e6cbf1832a3848d1051d060ba903b9f5e598322"
    )
    assert manifest["image"]["scan"]["sha256"] == (
        "125f299ca63447f56581cda452a878ba3c3189b6afb7bfd15917bedd44afc28c"
    )
    assert manifest["required_loader_features"] == ["CALL", "COPY"]
    assert [record["offset"] for record in manifest["records"]] == [0, 9, 24, 31, 46]
    assert [record["name"] for record in manifest["records"]] == [
        "COPY", "COPY", "CALL", "COPY", "CALL"
    ]


def test_manifest_json_is_deterministic(tmp_path):
    _, _, manifest_path, manifest = make_artifact(tmp_path)
    first = manifest_path.read_bytes()
    write_manifest(manifest_path, manifest)
    second = manifest_path.read_bytes()
    assert first == second
    assert first.endswith(b"\n")


def test_raw_binary_tamper_is_rejected(tmp_path):
    raw_path, _, manifest_path, _ = make_artifact(tmp_path)
    raw = bytearray(raw_path.read_bytes())
    raw[0] ^= 1
    raw_path.write_bytes(raw)
    with pytest.raises(ManifestError, match="raw binary size or SHA-256 mismatch"):
        validate_manifest_file(manifest_path)


def test_scan_tamper_is_rejected(tmp_path):
    _, scan_path, manifest_path, _ = make_artifact(tmp_path)
    scan = bytearray(scan_path.read_bytes())
    scan[4] ^= 1
    scan_path.write_bytes(scan)
    with pytest.raises(ManifestError, match="SCAN file size or SHA-256 mismatch"):
        validate_manifest_file(manifest_path)


def test_record_inventory_tamper_is_rejected(tmp_path):
    _, _, manifest_path, manifest = make_artifact(tmp_path)
    tampered = copy.deepcopy(manifest)
    tampered["records"][0]["payload_size"] += 1
    write_manifest(manifest_path, tampered)
    with pytest.raises(ManifestError, match="record inventory"):
        validate_manifest_file(manifest_path)


def test_required_features_tamper_is_rejected(tmp_path):
    _, _, manifest_path, manifest = make_artifact(tmp_path)
    tampered = copy.deepcopy(manifest)
    tampered["required_loader_features"] = ["COPY"]
    write_manifest(manifest_path, tampered)
    with pytest.raises(ManifestError, match="required_loader_features"):
        validate_manifest_file(manifest_path)


def test_load_and_entry_metadata_must_match_scan(tmp_path):
    _, _, manifest_path, manifest = make_artifact(tmp_path)

    wrong_load = copy.deepcopy(manifest)
    wrong_load["image"]["load_address"] = 0x1200
    write_manifest(manifest_path, wrong_load)
    with pytest.raises(ManifestError, match="COPY the raw binary"):
        validate_manifest_file(manifest_path)

    wrong_entry = copy.deepcopy(manifest)
    wrong_entry["image"]["entry_point"] = 0x1200
    write_manifest(manifest_path, wrong_entry)
    with pytest.raises(ManifestError, match="CALL or JUMP"):
        validate_manifest_file(manifest_path)


def test_path_traversal_and_absolute_paths_are_rejected(tmp_path):
    _, _, manifest_path, manifest = make_artifact(tmp_path)

    traversal = copy.deepcopy(manifest)
    traversal["image"]["raw_binary"]["path"] = "../setup_stub.bin"
    with pytest.raises(ManifestError, match="safe relative path"):
        validate_manifest_data(traversal, manifest_path, verify_files=False)

    absolute = copy.deepcopy(manifest)
    absolute["image"]["scan"]["path"] = "/tmp/setup_stub.scan"
    with pytest.raises(ManifestError, match="safe relative path"):
        validate_manifest_data(absolute, manifest_path, verify_files=False)

    windows = copy.deepcopy(manifest)
    windows["image"]["scan"]["path"] = "build\\setup_stub.scan"
    with pytest.raises(ManifestError, match="POSIX separators"):
        validate_manifest_data(windows, manifest_path, verify_files=False)


def test_unknown_schema_byte_order_and_target_are_rejected(tmp_path):
    _, _, manifest_path, manifest = make_artifact(tmp_path)

    bad_version = copy.deepcopy(manifest)
    bad_version["schema_version"] = 2
    with pytest.raises(ManifestError, match="unsupported manifest schema"):
        validate_manifest_data(bad_version, manifest_path, verify_files=False)

    bad_order = copy.deepcopy(manifest)
    bad_order["byte_order"] = "big"
    with pytest.raises(ManifestError, match="unsupported byte_order"):
        validate_manifest_data(bad_order, manifest_path, verify_files=False)

    bad_target = copy.deepcopy(manifest)
    bad_target["target"]["device"] = "OTHER"
    with pytest.raises(ManifestError, match="unsupported target"):
        validate_manifest_data(bad_target, manifest_path, verify_files=False)


def test_missing_artifact_file_is_rejected(tmp_path):
    raw_path, _, manifest_path, _ = make_artifact(tmp_path)
    raw_path.unlink()
    with pytest.raises(ManifestError, match="artifact file is missing"):
        validate_manifest_file(manifest_path)


def test_build_rejects_artifacts_outside_manifest_directory(tmp_path):
    artifacts = tmp_path / "artifacts"
    manifests = tmp_path / "manifests"
    artifacts.mkdir()
    manifests.mkdir()
    raw, _, _ = assemble(SETUP_SOURCE, base=0x1000)
    raw_path = artifacts / "setup.bin"
    scan_path = artifacts / "setup.scan"
    raw_path.write_bytes(raw)
    scan_path.write_bytes(wrap_payload(raw, 0x1000))

    with pytest.raises(ManifestError, match="must be inside manifest directory"):
        build_manifest(
            raw_path,
            scan_path,
            manifests / "setup.json",
            load_address=0x1000,
            entry_point=0x1000,
            execution_model="bios-cooperative",
            target_device="CY7C67200",
            producer_repository="mark-e-deyoung/CY16-bootstrap",
            producer_commit=PRODUCER_COMMIT,
        )


def test_nonzero_scan_tail_is_rejected_during_generation(tmp_path):
    raw, _, _ = assemble(SETUP_SOURCE, base=0x1000)
    raw_path = tmp_path / "setup.bin"
    scan_path = tmp_path / "setup.scan"
    manifest_path = tmp_path / "setup.json"
    raw_path.write_bytes(raw)
    scan_path.write_bytes(wrap_payload(raw, 0x1000) + b"\x01")

    with pytest.raises(ManifestError, match="non-zero bytes"):
        build_manifest(
            raw_path,
            scan_path,
            manifest_path,
            load_address=0x1000,
            entry_point=0x1000,
            execution_model="bios-cooperative",
            target_device="CY7C67200",
            producer_repository="mark-e-deyoung/CY16-bootstrap",
            producer_commit=PRODUCER_COMMIT,
        )


def test_write_config_inventory_and_warning(tmp_path):
    raw = b"\x34\x12"
    scan = b"".join(
        [
            make_record(SCAN_OP_COPY, 0x1000, raw),
            make_config_record(0x3A, 0x2222),
            make_record(SCAN_OP_CALL, 0x1000),
            b"\x00\x00",
        ]
    )
    raw_path = tmp_path / "config.bin"
    scan_path = tmp_path / "config.scan"
    manifest_path = tmp_path / "config.json"
    raw_path.write_bytes(raw)
    scan_path.write_bytes(scan)

    manifest = build_manifest(
        raw_path,
        scan_path,
        manifest_path,
        load_address=0x1000,
        entry_point=0x1000,
        execution_model="standalone",
        target_device="CY7C67200",
        producer_repository="mark-e-deyoung/CY16-bootstrap",
        producer_commit=PRODUCER_COMMIT,
        tool_version="0.1.0-test",
    )
    config = manifest["records"][1]
    assert config["name"] == "WRITE_CONFIG"
    assert config["address"] == 0xC03A
    assert config["config_offset"] == 0x3A
    assert config["value"] == 0x2222
    assert "WRITE_CONFIG" in manifest["required_loader_features"]
    assert any("does not authorize execution" in item for item in manifest["warnings"])


def test_checked_hashes_match_actual_files(tmp_path):
    raw_path, scan_path, _, manifest = make_artifact(tmp_path)
    assert manifest["image"]["raw_binary"]["sha256"] == hashlib.sha256(
        raw_path.read_bytes()
    ).hexdigest()
    assert manifest["image"]["scan"]["sha256"] == hashlib.sha256(
        scan_path.read_bytes()
    ).hexdigest()
