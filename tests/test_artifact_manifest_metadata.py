from __future__ import annotations

import copy

import pytest

from cy16boot.artifact_manifest import ManifestError, validate_manifest_data

SHA = "0" * 64
COMMIT = "1" * 40


def record(
    index: int,
    offset: int,
    opcode: int,
    name: str,
    encoded_length: int,
    address: int,
    payload_size: int,
    **extra: int,
) -> dict:
    item = {
        "index": index,
        "offset": offset,
        "opcode": opcode,
        "name": name,
        "encoded_length": encoded_length,
        "record_size": encoded_length + 5,
        "address": address,
        "payload_size": payload_size,
        "payload_sha256": SHA,
    }
    item.update(extra)
    return item


def canonical_manifest() -> dict:
    records = [
        record(0, 0, 0x00, "COPY", 4, 0x00E0, 2),
        record(1, 9, 0x00, "COPY", 10, 0x1000, 8),
        record(2, 24, 0x05, "CALL", 2, 0x1000, 0),
        record(3, 31, 0x00, "COPY", 10, 0x1000, 8),
        record(4, 46, 0x05, "CALL", 2, 0x1000, 0),
    ]
    return {
        "schema": "cy16-scan-artifact/v1",
        "schema_version": 1,
        "artifact_kind": "cy16-scan-image",
        "target": {"family": "C67x00", "device": "CY7C67200"},
        "execution_model": "bios-cooperative",
        "byte_order": "little",
        "producer": {
            "repository": "mark-e-deyoung/CY16-bootstrap",
            "commit": COMMIT,
            "tool": "cy16-scan-manifest",
            "version": "0.1.0-test",
        },
        "image": {
            "load_address": 0x1000,
            "entry_point": 0x1000,
            "raw_binary": {"path": "image.bin", "size": 8, "sha256": SHA},
            "scan": {"path": "image.scan", "size": 55, "sha256": SHA},
        },
        "records": records,
        "required_loader_features": ["CALL", "COPY"],
        "constraints": [],
        "warnings": [],
        "provenance_notes": [],
    }


def config_manifest() -> dict:
    manifest = canonical_manifest()
    manifest["image"]["raw_binary"]["size"] = 2
    manifest["image"]["scan"]["size"] = 24
    manifest["records"] = [
        record(0, 0, 0x00, "COPY", 4, 0x1000, 2),
        record(
            1,
            9,
            0x09,
            "WRITE_CONFIG",
            3,
            0xC03A,
            2,
            config_offset=0x3A,
            value=0x2222,
        ),
        record(2, 17, 0x05, "CALL", 2, 0x1000, 0),
    ]
    manifest["required_loader_features"] = ["CALL", "COPY", "WRITE_CONFIG"]
    return manifest


def validate_metadata(manifest: dict) -> dict:
    return validate_manifest_data(
        manifest,
        "unused/manifest.json",
        verify_files=False,
    )


def test_valid_metadata_only_manifest_passes() -> None:
    manifest = canonical_manifest()
    assert validate_metadata(manifest) is manifest


def test_record_size_must_equal_encoded_length_plus_header() -> None:
    manifest = canonical_manifest()
    manifest["records"][0]["record_size"] += 1
    with pytest.raises(ManifestError, match="record_size must equal encoded_length"):
        validate_metadata(manifest)


def test_record_offsets_must_be_contiguous_from_zero() -> None:
    manifest = canonical_manifest()
    manifest["records"][0]["offset"] = 1
    with pytest.raises(ManifestError, match="contiguous offset 0"):
        validate_metadata(manifest)

    manifest = canonical_manifest()
    manifest["records"][2]["offset"] += 2
    with pytest.raises(ManifestError, match="contiguous offset 24"):
        validate_metadata(manifest)


def test_copy_length_must_match_payload_size() -> None:
    manifest = canonical_manifest()
    manifest["records"][1]["payload_size"] = 7
    with pytest.raises(ManifestError, match="COPY length"):
        validate_metadata(manifest)


def test_call_and_jump_must_have_exact_empty_shape() -> None:
    for opcode, name in ((0x05, "CALL"), (0x04, "JUMP")):
        manifest = canonical_manifest()
        target = manifest["records"][2]
        target["opcode"] = opcode
        target["name"] = name
        target["encoded_length"] = 3
        target["record_size"] = 8
        target["payload_size"] = 1
        for later in manifest["records"][3:]:
            later["offset"] += 1
        manifest["required_loader_features"] = sorted({
            item["name"] for item in manifest["records"]
        })
        with pytest.raises(ManifestError, match=f"{name} must have length 2"):
            validate_metadata(manifest)


def test_known_opcode_name_must_be_canonical() -> None:
    manifest = canonical_manifest()
    manifest["records"][0]["name"] = "DATA"
    manifest["required_loader_features"] = ["CALL", "COPY", "DATA"]
    with pytest.raises(ManifestError, match="name must be COPY"):
        validate_metadata(manifest)


def test_write_config_metadata_relationships() -> None:
    assert validate_metadata(config_manifest())

    manifest = config_manifest()
    manifest["records"][1]["address"] = 0xC03B
    with pytest.raises(ManifestError, match="address disagrees with config_offset"):
        validate_metadata(manifest)

    manifest = config_manifest()
    config = manifest["records"][1]
    config["encoded_length"] = 4
    config["record_size"] = 9
    for later in manifest["records"][2:]:
        later["offset"] += 1
    with pytest.raises(ManifestError, match="WRITE_CONFIG must have length 3"):
        validate_metadata(manifest)


def test_feature_list_must_match_metadata_record_names() -> None:
    manifest = canonical_manifest()
    manifest["required_loader_features"] = ["COPY"]
    with pytest.raises(ManifestError, match="record metadata"):
        validate_metadata(manifest)


def test_unknown_opcode_is_explicit_generic_address_record() -> None:
    manifest = canonical_manifest()
    unknown = manifest["records"][0]
    unknown["opcode"] = 0x7E
    unknown["name"] = "OP_0x7e"
    manifest["required_loader_features"] = ["CALL", "COPY", "OP_0x7e"]
    assert validate_metadata(manifest)

    unknown["encoded_length"] = 3
    unknown["record_size"] = 8
    for later in manifest["records"][1:]:
        later["offset"] -= 1
    with pytest.raises(ManifestError, match="unknown address record length"):
        validate_metadata(manifest)
