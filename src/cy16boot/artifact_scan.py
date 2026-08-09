from __future__ import annotations

import argparse
import hashlib
import json
import os
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, Iterable

SCHEMA_ID = "cy16-legacy-artifact-scan/v1"
SCHEMA_VERSION = 1
DEFAULT_CONTENT_MAX_BYTES = 16 * 1024 * 1024

# Exact names, path fragments, symbols, and package fingerprints recovered from
# Cypress/Infineon documents, forum references, Xilinx answer-record leads, and
# surviving public implementations. Matching is case-insensitive.
FINGERPRINTS: dict[str, tuple[str, ...]] = {
    "file_name": (
        "ISRS.S",
        "cy7c67200_300.h",
        "cy7C67200_300.h",
        "cy7c67200_300_hcd.c",
        "cy7c67200_300_hcd_simple.c",
        "cy7c67200_300_lcp.c",
        "cy7c67200_300_lcd.c",
        "de1_bios.asm",
        "ml40x_usb.zip",
        "msc_scan.bin",
        "scanwrp2",
        "scanwrap.c",
        "BAL.ld",
        "StartupNoBIOS.s",
        "StartupWithBIOS.s",
    ),
    "path_fragment": (
        "Cypress/USB/OTG-Host",
        "Cypress\\USB\\OTG-Host",
        "Source/coprocessor/de_app",
        "Source\\coprocessor\\de_app",
        "Source/coprocessor/linux/drivers/usb/cy7c67300",
        "Source\\coprocessor\\linux\\drivers\\usb\\cy7c67300",
        "Common/ISRS.S",
        "Common\\ISRS.S",
        "usbd/dedev/de1_bios.asm",
        "usbd\\dedev\\de1_bios.asm",
    ),
    "content_symbol": (
        "COMM_CTRL_REG_ADDR",
        "COMM_CTRL_REG_DATA",
        "COMM_LAST_DATA",
        "COMM_READ_CTRL_REG",
        "COMM_WRITE_CTRL_REG",
        "hcd_irq_resume",
        "DEFAULT_EOT",
        "MAX_FRAME_BW",
        "HUSB_SIE1_INIT_INT",
        "HUSB_RESET_INT",
        "CY3663",
        "CY4640",
        "cy16-elf-gcc",
        "cy16-elf-as",
        "cy16-elf-ld",
        "cy16-elf-objdump",
        "cy16-elf-objcopy",
    ),
}

ARCHIVE_SUFFIXES = {
    ".zip": "zip",
    ".tar": "tar",
    ".tgz": "tar",
    ".gz": "tar",
    ".bz2": "tar",
    ".xz": "tar",
}


class ScanError(ValueError):
    """Raised for unsafe or invalid scanner inputs."""


@dataclass(frozen=True)
class Match:
    root: str
    location: str
    container: str | None
    kind: str
    fingerprint_class: str
    fingerprint: str
    size: int
    sha256: str | None
    archive_member_crc32: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "location": self.location,
            "container": self.container,
            "kind": self.kind,
            "fingerprint_class": self.fingerprint_class,
            "fingerprint": self.fingerprint,
            "size": self.size,
            "sha256": self.sha256,
            "archive_member_crc32": self.archive_member_crc32,
        }


def _sha256_stream(stream: BinaryIO, limit: int | None = None) -> str:
    digest = hashlib.sha256()
    remaining = limit
    while True:
        request = 1024 * 1024 if remaining is None else min(1024 * 1024, remaining)
        if request <= 0:
            break
        block = stream.read(request)
        if not block:
            break
        digest.update(block)
        if remaining is not None:
            remaining -= len(block)
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return _sha256_stream(stream)


def _normalized(text: str) -> str:
    return text.replace("\\", "/").casefold()


def _name_matches(location: str) -> list[tuple[str, str]]:
    normalized = _normalized(location)
    basename = PurePosixPath(normalized).name
    matches: list[tuple[str, str]] = []
    for fingerprint in FINGERPRINTS["file_name"]:
        if basename == fingerprint.casefold():
            matches.append(("file_name", fingerprint))
    for fingerprint in FINGERPRINTS["path_fragment"]:
        if _normalized(fingerprint) in normalized:
            matches.append(("path_fragment", fingerprint))
    return matches


def _content_matches(data: bytes) -> list[tuple[str, str]]:
    lowered = data.lower()
    matches: list[tuple[str, str]] = []
    for fingerprint in FINGERPRINTS["content_symbol"]:
        if fingerprint.encode("ascii").lower() in lowered:
            matches.append(("content_symbol", fingerprint))
    return matches


def _safe_member_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return f"UNSAFE:{normalized}"
    return str(path)


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _scan_regular_file(
    path: Path,
    root: Path,
    *,
    content_scan: bool,
    content_max_bytes: int,
) -> list[Match]:
    relative = _relative(path, root)
    size = path.stat().st_size
    found: list[Match] = []
    name_hits = _name_matches(relative)
    content_hits: list[tuple[str, str]] = []
    if content_scan and size <= content_max_bytes:
        try:
            content_hits = _content_matches(path.read_bytes())
        except OSError:
            content_hits = []
    hits = name_hits + content_hits
    if not hits:
        return []
    digest = _sha256_file(path)
    for fingerprint_class, fingerprint in sorted(set(hits)):
        found.append(
            Match(
                root=root.resolve().as_posix(),
                location=relative,
                container=None,
                kind="file",
                fingerprint_class=fingerprint_class,
                fingerprint=fingerprint,
                size=size,
                sha256=digest,
            )
        )
    return found


def _scan_zip(
    path: Path,
    root: Path,
    *,
    content_scan: bool,
    content_max_bytes: int,
) -> list[Match]:
    found: list[Match] = []
    container = _relative(path, root)
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile):
        return found
    with archive:
        for info in sorted(archive.infolist(), key=lambda item: item.filename.casefold()):
            if info.is_dir():
                continue
            member = _safe_member_name(info.filename)
            name_hits = _name_matches(member)
            content_hits: list[tuple[str, str]] = []
            digest: str | None = None
            if content_scan and info.file_size <= content_max_bytes:
                try:
                    with archive.open(info, "r") as stream:
                        data = stream.read(content_max_bytes + 1)
                    if len(data) <= content_max_bytes:
                        content_hits = _content_matches(data)
                        if name_hits or content_hits:
                            digest = hashlib.sha256(data).hexdigest()
                except (OSError, RuntimeError, zipfile.BadZipFile):
                    content_hits = []
            if name_hits and digest is None and info.file_size <= content_max_bytes:
                try:
                    with archive.open(info, "r") as stream:
                        digest = _sha256_stream(stream)
                except (OSError, RuntimeError, zipfile.BadZipFile):
                    digest = None
            for fingerprint_class, fingerprint in sorted(set(name_hits + content_hits)):
                found.append(
                    Match(
                        root=root.resolve().as_posix(),
                        location=member,
                        container=container,
                        kind="zip-member",
                        fingerprint_class=fingerprint_class,
                        fingerprint=fingerprint,
                        size=info.file_size,
                        sha256=digest,
                        archive_member_crc32=f"{info.CRC:08x}",
                    )
                )
    return found


def _scan_tar(
    path: Path,
    root: Path,
    *,
    content_scan: bool,
    content_max_bytes: int,
) -> list[Match]:
    found: list[Match] = []
    container = _relative(path, root)
    try:
        archive = tarfile.open(path, "r:*")
    except (OSError, tarfile.TarError):
        return found
    with archive:
        members = sorted(archive.getmembers(), key=lambda item: item.name.casefold())
        for info in members:
            if not info.isfile():
                continue
            member = _safe_member_name(info.name)
            name_hits = _name_matches(member)
            content_hits: list[tuple[str, str]] = []
            digest: str | None = None
            if (content_scan or name_hits) and info.size <= content_max_bytes:
                try:
                    stream = archive.extractfile(info)
                    if stream is not None:
                        with stream:
                            data = stream.read(content_max_bytes + 1)
                        if len(data) <= content_max_bytes:
                            if content_scan:
                                content_hits = _content_matches(data)
                            if name_hits or content_hits:
                                digest = hashlib.sha256(data).hexdigest()
                except (OSError, tarfile.TarError):
                    content_hits = []
            for fingerprint_class, fingerprint in sorted(set(name_hits + content_hits)):
                found.append(
                    Match(
                        root=root.resolve().as_posix(),
                        location=member,
                        container=container,
                        kind="tar-member",
                        fingerprint_class=fingerprint_class,
                        fingerprint=fingerprint,
                        size=info.size,
                        sha256=digest,
                    )
                )
    return found


def _archive_kind(path: Path) -> str | None:
    lower = path.name.casefold()
    if lower.endswith(".tar.gz") or lower.endswith(".tar.bz2") or lower.endswith(".tar.xz"):
        return "tar"
    return ARCHIVE_SUFFIXES.get(path.suffix.casefold())


def scan_roots(
    roots: Iterable[str | Path],
    *,
    inspect_archives: bool = True,
    content_scan: bool = False,
    content_max_bytes: int = DEFAULT_CONTENT_MAX_BYTES,
) -> dict[str, Any]:
    normalized_roots: list[Path] = []
    for root_value in roots:
        root = Path(root_value).expanduser().resolve()
        if not root.exists():
            raise ScanError(f"scan root does not exist: {root}")
        normalized_roots.append(root)
    if content_max_bytes < 0:
        raise ScanError("content_max_bytes must be non-negative")

    matches: list[Match] = []
    scanned_files = 0
    scanned_archives = 0
    errors: list[dict[str, str]] = []

    for root in sorted(normalized_roots, key=lambda item: item.as_posix().casefold()):
        candidates = [root] if root.is_file() else sorted(
            (path for path in root.rglob("*") if path.is_file()),
            key=lambda item: item.as_posix().casefold(),
        )
        for path in candidates:
            scanned_files += 1
            try:
                matches.extend(
                    _scan_regular_file(
                        path,
                        root if root.is_dir() else root.parent,
                        content_scan=content_scan,
                        content_max_bytes=content_max_bytes,
                    )
                )
                archive_kind = _archive_kind(path)
                if inspect_archives and archive_kind:
                    scanned_archives += 1
                    archive_root = root if root.is_dir() else root.parent
                    if archive_kind == "zip":
                        matches.extend(
                            _scan_zip(
                                path,
                                archive_root,
                                content_scan=content_scan,
                                content_max_bytes=content_max_bytes,
                            )
                        )
                    else:
                        matches.extend(
                            _scan_tar(
                                path,
                                archive_root,
                                content_scan=content_scan,
                                content_max_bytes=content_max_bytes,
                            )
                        )
            except (OSError, PermissionError) as exc:
                errors.append({"path": path.as_posix(), "error": str(exc)})

    unique = {
        (
            match.root,
            match.location,
            match.container,
            match.kind,
            match.fingerprint_class,
            match.fingerprint,
        ): match
        for match in matches
    }
    ordered = sorted(
        unique.values(),
        key=lambda match: (
            match.root.casefold(),
            (match.container or "").casefold(),
            match.location.casefold(),
            match.fingerprint_class,
            match.fingerprint.casefold(),
        ),
    )
    return {
        "schema": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "scanner": {
            "inspect_archives": inspect_archives,
            "content_scan": content_scan,
            "content_max_bytes": content_max_bytes,
        },
        "roots": [root.as_posix() for root in normalized_roots],
        "fingerprints": {
            key: list(values) for key, values in sorted(FINGERPRINTS.items())
        },
        "summary": {
            "files_scanned": scanned_files,
            "archives_inspected": scanned_archives,
            "matches": len(ordered),
            "errors": len(errors),
        },
        "matches": [match.to_json() for match in ordered],
        "errors": sorted(errors, key=lambda item: item["path"].casefold()),
    }


def write_report(path: str | Path, report: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inventory local media for CY16/CY7C67200 legacy artifacts"
    )
    parser.add_argument("roots", nargs="+", help="files or directory trees to scan")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument(
        "--no-archives",
        action="store_true",
        help="do not inspect ZIP/TAR member names",
    )
    parser.add_argument(
        "--content",
        action="store_true",
        help="scan small file/member contents for exact ASCII symbols",
    )
    parser.add_argument(
        "--content-max-bytes",
        type=int,
        default=DEFAULT_CONTENT_MAX_BYTES,
    )
    args = parser.parse_args(argv)
    try:
        report = scan_roots(
            args.roots,
            inspect_archives=not args.no_archives,
            content_scan=args.content,
            content_max_bytes=args.content_max_bytes,
        )
    except ScanError as exc:
        parser.error(str(exc))
        return 2
    write_report(args.output, report)
    print(
        f"scanned={report['summary']['files_scanned']} "
        f"archives={report['summary']['archives_inspected']} "
        f"matches={report['summary']['matches']} "
        f"errors={report['summary']['errors']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
