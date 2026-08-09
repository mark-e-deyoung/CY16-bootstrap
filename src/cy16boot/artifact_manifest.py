from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from .common import le_to_word, read_bytes
from .scan import (
    SCAN_OP_CALL,
    SCAN_OP_COPY,
    SCAN_OP_JUMP,
    SCAN_OP_WRITE_CONFIG,
    ScanRecord,
    parse_scan,
)

SCHEMA_ID = "cy16-scan-artifact/v1"
SCHEMA_VERSION = 1
ARTIFACT_KIND = "cy16-scan-image"
BYTE_ORDER = "little"
EXECUTION_MODELS = {"bios-cooperative", "standalone", "unknown"}
TARGET_DEVICES = {"CY7C67200", "CY7C67300"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class ManifestError(ValueError):
    """Raised when a CY16 SCAN artifact manifest is invalid."""


def _tool_version() -> str:
    try:
        return importlib.metadata.version("cy16-compiler-bootstrap")
    except importlib.metadata.PackageNotFoundError:
        return "0.1.0"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_int(name: str, value: Any, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ManifestError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ManifestError(f"{name} must be in {minimum}..{maximum}")
    return value


def _require_str(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{name} must be a non-empty string")
    return value


def _require_exact_keys(name: str, value: dict[str, Any], allowed: set[str], required: set[str]) -> None:
    missing = required - value.keys()
    extra = value.keys() - allowed
    if missing:
        raise ManifestError(f"{name} missing keys: {', '.join(sorted(missing))}")
    if extra:
        raise ManifestError(f"{name} has unknown keys: {', '.join(sorted(extra))}")


def _safe_relative_path(name: str, value: Any) -> PurePosixPath:
    text = _require_str(name, value)
    if "\\" in text:
        raise ManifestError(f"{name} must use POSIX separators")
    path = PurePosixPath(text)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ManifestError(f"{name} must be a safe relative path")
    return path


def _relative_artifact_path(path: Path, manifest_dir: Path) -> str:
    resolved = path.resolve()
    base = manifest_dir.resolve()
    try:
        relative = resolved.relative_to(base)
    except ValueError as exc:
        raise ManifestError(
            f"artifact {resolved} must be inside manifest directory {base}"
        ) from exc
    return relative.as_posix()


def _strict_scan_records(scan_data: bytes) -> list[ScanRecord]:
    records = parse_scan(scan_data)
    if not records:
        raise ManifestError("SCAN image contains no records")
    consumed = records[-1].offset + records[-1].size
    tail = scan_data[consumed:]
    if any(tail):
        raise ManifestError("SCAN image has non-zero bytes after the final record")
    return records


def _record_manifest(index: int, record: ScanRecord) -> dict[str, Any]:
    item: dict[str, Any] = {
        "index": index,
        "offset": record.offset,
        "opcode": record.opcode,
        "name": record.name,
        "encoded_length": record.length,
        "record_size": record.size,
        "address": record.address,
        "payload_size": len(record.payload),
        "payload_sha256": _sha256(record.payload),
    }
    if record.opcode == SCAN_OP_WRITE_CONFIG:
        item["config_offset"] = record.address & 0xFF
        item["value"] = le_to_word(record.payload, 0)
    return item


def _record_inventory(records: Iterable[ScanRecord]) -> list[dict[str, Any]]:
    return [_record_manifest(index, record) for index, record in enumerate(records)]


def _required_loader_features(records: Iterable[ScanRecord]) -> list[str]:
    return sorted({record.name for record in records})


def _file_descriptor(path_text: str, data: bytes) -> dict[str, Any]:
    return {
        "path": path_text,
        "size": len(data),
        "sha256": _sha256(data),
    }


def _has_raw_copy(records: Iterable[ScanRecord], load_address: int, raw_data: bytes) -> bool:
    return any(
        record.opcode == SCAN_OP_COPY
        and record.address == load_address
        and record.payload == raw_data
        for record in records
    )


def _has_entry_transfer(records: Iterable[ScanRecord], entry_point: int) -> bool:
    return any(
        record.opcode in {SCAN_OP_CALL, SCAN_OP_JUMP}
        and record.address == entry_point
        for record in records
    )


def build_manifest(
    raw_path: str | Path,
    scan_path: str | Path,
    manifest_path: str | Path,
    *,
    load_address: int,
    entry_point: int,
    execution_model: str,
    target_device: str,
    producer_repository: str,
    producer_commit: str,
    tool_version: str | None = None,
    warnings: Iterable[str] = (),
    constraints: Iterable[str] = (),
    provenance_notes: Iterable[str] = (),
) -> dict[str, Any]:
    raw = Path(raw_path)
    scan = Path(scan_path)
    output = Path(manifest_path)
    manifest_dir = output.parent

    load_address = _require_int("load_address", load_address, 0, 0xFFFF)
    entry_point = _require_int("entry_point", entry_point, 0, 0xFFFF)
    if load_address & 1 or entry_point & 1:
        raise ManifestError("load_address and entry_point must be word aligned")
    if execution_model not in EXECUTION_MODELS:
        raise ManifestError(f"unsupported execution_model: {execution_model}")
    if target_device not in TARGET_DEVICES:
        raise ManifestError(f"unsupported target device: {target_device}")
    _require_str("producer_repository", producer_repository)
    if not COMMIT_RE.fullmatch(producer_commit):
        raise ManifestError("producer_commit must be a lowercase 40-character hex SHA")

    raw_data = read_bytes(raw)
    scan_data = read_bytes(scan)
    records = _strict_scan_records(scan_data)
    if not _has_raw_copy(records, load_address, raw_data):
        raise ManifestError("SCAN image does not COPY the raw binary at load_address")
    if not _has_entry_transfer(records, entry_point):
        raise ManifestError("SCAN image does not CALL or JUMP to entry_point")

    manifest = {
        "schema": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": ARTIFACT_KIND,
        "target": {
            "family": "C67x00",
            "device": target_device,
        },
        "execution_model": execution_model,
        "byte_order": BYTE_ORDER,
        "producer": {
            "repository": producer_repository,
            "commit": producer_commit,
            "tool": "cy16-scan-manifest",
            "version": tool_version or _tool_version(),
        },
        "image": {
            "load_address": load_address,
            "entry_point": entry_point,
            "raw_binary": _file_descriptor(
                _relative_artifact_path(raw, manifest_dir), raw_data
            ),
            "scan": _file_descriptor(
                _relative_artifact_path(scan, manifest_dir), scan_data
            ),
        },
        "records": _record_inventory(records),
        "required_loader_features": _required_loader_features(records),
        "constraints": list(constraints),
        "warnings": list(warnings),
        "provenance_notes": list(provenance_notes),
    }

    if any(record.opcode == SCAN_OP_WRITE_CONFIG for record in records):
        warning = (
            "WRITE_CONFIG requires a policy-gated COMM_WRITE_CTRL_REG consumer; "
            "this manifest does not authorize execution."
        )
        if warning not in manifest["warnings"]:
            manifest["warnings"].append(warning)

    validate_manifest_data(manifest, output, verify_files=True)
    return manifest


def write_manifest(path: str | Path, manifest: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _validate_string_list(name: str, value: Any) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ManifestError(f"{name} must be a list of strings")
    return value


def _validate_file_descriptor(name: str, value: Any) -> tuple[PurePosixPath, int, str]:
    if not isinstance(value, dict):
        raise ManifestError(f"{name} must be an object")
    _require_exact_keys(
        name,
        value,
        {"path", "size", "sha256"},
        {"path", "size", "sha256"},
    )
    path = _safe_relative_path(f"{name}.path", value["path"])
    size = _require_int(f"{name}.size", value["size"], 0, 0xFFFFFFFF)
    digest = _require_str(f"{name}.sha256", value["sha256"])
    if not SHA256_RE.fullmatch(digest):
        raise ManifestError(f"{name}.sha256 must be lowercase SHA-256 hex")
    return path, size, digest


def _validate_record_shape(index: int, value: Any) -> dict[str, Any]:
    name = f"records[{index}]"
    if not isinstance(value, dict):
        raise ManifestError(f"{name} must be an object")
    allowed = {
        "index", "offset", "opcode", "name", "encoded_length", "record_size",
        "address", "payload_size", "payload_sha256", "config_offset", "value",
    }
    required = {
        "index", "offset", "opcode", "name", "encoded_length", "record_size",
        "address", "payload_size", "payload_sha256",
    }
    _require_exact_keys(name, value, allowed, required)
    if value["index"] != index:
        raise ManifestError(f"{name}.index must equal its array position")
    _require_int(f"{name}.offset", value["offset"], 0, 0xFFFFFFFF)
    opcode = _require_int(f"{name}.opcode", value["opcode"], 0, 0xFF)
    _require_str(f"{name}.name", value["name"])
    _require_int(f"{name}.encoded_length", value["encoded_length"], 1, 0xFFFF)
    _require_int(f"{name}.record_size", value["record_size"], 6, 0x10004)
    _require_int(f"{name}.address", value["address"], 0, 0xFFFF)
    _require_int(f"{name}.payload_size", value["payload_size"], 0, 0xFFFF)
    digest = _require_str(f"{name}.payload_sha256", value["payload_sha256"])
    if not SHA256_RE.fullmatch(digest):
        raise ManifestError(f"{name}.payload_sha256 must be lowercase SHA-256 hex")
    if opcode == SCAN_OP_WRITE_CONFIG:
        if "config_offset" not in value or "value" not in value:
            raise ManifestError(f"{name} missing WRITE_CONFIG fields")
        _require_int(f"{name}.config_offset", value["config_offset"], 0, 0xFF)
        _require_int(f"{name}.value", value["value"], 0, 0xFFFF)
    elif "config_offset" in value or "value" in value:
        raise ManifestError(f"{name} has WRITE_CONFIG-only fields")
    return value


def validate_manifest_data(
    manifest: Any,
    manifest_path: str | Path,
    *,
    verify_files: bool = True,
) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise ManifestError("manifest must be a JSON object")
    top_keys = {
        "schema", "schema_version", "artifact_kind", "target", "execution_model",
        "byte_order", "producer", "image", "records", "required_loader_features",
        "constraints", "warnings", "provenance_notes",
    }
    _require_exact_keys("manifest", manifest, top_keys, top_keys)

    if manifest["schema"] != SCHEMA_ID or manifest["schema_version"] != SCHEMA_VERSION:
        raise ManifestError("unsupported manifest schema or schema version")
    if manifest["artifact_kind"] != ARTIFACT_KIND:
        raise ManifestError("unsupported artifact_kind")
    if manifest["execution_model"] not in EXECUTION_MODELS:
        raise ManifestError("unsupported execution_model")
    if manifest["byte_order"] != BYTE_ORDER:
        raise ManifestError("unsupported byte_order")

    target = manifest["target"]
    if not isinstance(target, dict):
        raise ManifestError("target must be an object")
    _require_exact_keys("target", target, {"family", "device"}, {"family", "device"})
    if target["family"] != "C67x00" or target["device"] not in TARGET_DEVICES:
        raise ManifestError("unsupported target")

    producer = manifest["producer"]
    if not isinstance(producer, dict):
        raise ManifestError("producer must be an object")
    _require_exact_keys(
        "producer",
        producer,
        {"repository", "commit", "tool", "version"},
        {"repository", "commit", "tool", "version"},
    )
    _require_str("producer.repository", producer["repository"])
    if not COMMIT_RE.fullmatch(_require_str("producer.commit", producer["commit"])):
        raise ManifestError("producer.commit must be a lowercase 40-character hex SHA")
    if producer["tool"] != "cy16-scan-manifest":
        raise ManifestError("unsupported producer.tool")
    _require_str("producer.version", producer["version"])

    image = manifest["image"]
    if not isinstance(image, dict):
        raise ManifestError("image must be an object")
    _require_exact_keys(
        "image",
        image,
        {"load_address", "entry_point", "raw_binary", "scan"},
        {"load_address", "entry_point", "raw_binary", "scan"},
    )
    load_address = _require_int("image.load_address", image["load_address"], 0, 0xFFFF)
    entry_point = _require_int("image.entry_point", image["entry_point"], 0, 0xFFFF)
    if load_address & 1 or entry_point & 1:
        raise ManifestError("image addresses must be word aligned")
    raw_rel, raw_size, raw_digest = _validate_file_descriptor(
        "image.raw_binary", image["raw_binary"]
    )
    scan_rel, scan_size, scan_digest = _validate_file_descriptor(
        "image.scan", image["scan"]
    )

    records_value = manifest["records"]
    if not isinstance(records_value, list) or not records_value:
        raise ManifestError("records must be a non-empty list")
    for index, record in enumerate(records_value):
        _validate_record_shape(index, record)

    features = _validate_string_list(
        "required_loader_features", manifest["required_loader_features"]
    )
    if features != sorted(set(features)):
        raise ManifestError("required_loader_features must be sorted and unique")
    _validate_string_list("constraints", manifest["constraints"])
    _validate_string_list("warnings", manifest["warnings"])
    _validate_string_list("provenance_notes", manifest["provenance_notes"])

    if not verify_files:
        return manifest

    root = Path(manifest_path).resolve().parent
    raw_path = root.joinpath(*raw_rel.parts)
    scan_path = root.joinpath(*scan_rel.parts)
    if not raw_path.is_file() or not scan_path.is_file():
        raise ManifestError("manifest artifact file is missing")
    raw_data = read_bytes(raw_path)
    scan_data = read_bytes(scan_path)
    if len(raw_data) != raw_size or _sha256(raw_data) != raw_digest:
        raise ManifestError("raw binary size or SHA-256 mismatch")
    if len(scan_data) != scan_size or _sha256(scan_data) != scan_digest:
        raise ManifestError("SCAN file size or SHA-256 mismatch")

    scan_records = _strict_scan_records(scan_data)
    expected_inventory = _record_inventory(scan_records)
    if records_value != expected_inventory:
        raise ManifestError("SCAN record inventory does not match the SCAN file")
    expected_features = _required_loader_features(scan_records)
    if features != expected_features:
        raise ManifestError("required_loader_features do not match SCAN records")
    if not _has_raw_copy(scan_records, load_address, raw_data):
        raise ManifestError("SCAN image does not COPY the raw binary at load_address")
    if not _has_entry_transfer(scan_records, entry_point):
        raise ManifestError("SCAN image does not CALL or JUMP to entry_point")
    return manifest


def validate_manifest_file(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read manifest: {exc}") from exc
    return validate_manifest_data(manifest, manifest_path, verify_files=True)


def _create_command(args: argparse.Namespace) -> int:
    manifest = build_manifest(
        args.raw_binary,
        args.scan,
        args.output,
        load_address=int(args.load_address, 0),
        entry_point=int(args.entry_point, 0),
        execution_model=args.execution_model,
        target_device=args.target_device,
        producer_repository=args.producer_repository,
        producer_commit=args.producer_commit,
        tool_version=args.tool_version,
        warnings=args.warning,
        constraints=args.constraint,
        provenance_notes=args.provenance_note,
    )
    write_manifest(args.output, manifest)
    return 0


def _validate_command(args: argparse.Namespace) -> int:
    validate_manifest_file(args.manifest)
    print(f"valid: {args.manifest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or validate a CY16 SCAN artifact manifest")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="create a deterministic v1 manifest")
    create.add_argument("raw_binary")
    create.add_argument("scan")
    create.add_argument("output")
    create.add_argument("--load-address", required=True)
    create.add_argument("--entry-point", required=True)
    create.add_argument(
        "--execution-model", choices=sorted(EXECUTION_MODELS), required=True
    )
    create.add_argument(
        "--target-device", choices=sorted(TARGET_DEVICES), default="CY7C67200"
    )
    create.add_argument(
        "--producer-repository", default="mark-e-deyoung/CY16-bootstrap"
    )
    create.add_argument(
        "--producer-commit", default=os.environ.get("GITHUB_SHA"), required=False
    )
    create.add_argument("--tool-version", default=None)
    create.add_argument("--warning", action="append", default=[])
    create.add_argument("--constraint", action="append", default=[])
    create.add_argument("--provenance-note", action="append", default=[])
    create.set_defaults(func=_create_command)

    validate = subparsers.add_parser("validate", help="validate a v1 manifest and its files")
    validate.add_argument("manifest")
    validate.set_defaults(func=_validate_command)

    args = parser.parse_args(argv)
    if args.command == "create" and not args.producer_commit:
        parser.error("create requires --producer-commit or GITHUB_SHA")
    try:
        return args.func(args)
    except ManifestError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
