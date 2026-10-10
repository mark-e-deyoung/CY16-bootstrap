#!/usr/bin/env python3
"""Metadata-only inventory of the official Terasic DE2-115 Cypress System CD.

Public runner: never execute or upload vendor binaries. Stream a bounded ZIP
into temporary storage, hash and inventory it, then delete all raw bytes.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import zipfile

URL = ("https://download.terasic.com/downloads/cd-rom/de2-115/"
       "CD-ROM_Cypress_USB/DE2-115_v.3.0.6_SystemCD.zip")
MAX_ARCHIVE = 256 * 1024 * 1024
MAX_MEMBER_HASH = 8 * 1024 * 1024
MAX_HASHED_TOTAL = 48 * 1024 * 1024
KEYS = ("cyusb", "cypress", "cy7c", "usb_control", "usbcontrol",
        "nios_device", "ez-otg", "ez_otg", "driver", "usb_device")


def allowed(url: str) -> bool:
    parts = urlparse(url)
    return parts.scheme == "https" and parts.hostname == "download.terasic.com"


def acquire(path: Path) -> dict:
    if not allowed(URL):
        raise ValueError("unexpected target URL")
    sha = hashlib.sha256()
    total = 0
    req = Request(URL, headers={"User-Agent": "CY16-evidence-research/1 (metadata only)"})
    with urlopen(req, timeout=90) as response, path.open("wb") as output:
        if not allowed(response.geturl()):
            raise ValueError("redirect outside Terasic download host")
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_ARCHIVE:
                raise ValueError("download exceeds 256 MiB budget")
            sha.update(chunk)
            output.write(chunk)
        return {"resolved_url": response.geturl(), "bytes": total,
                "sha256": sha.hexdigest(), "content_type": response.headers.get("Content-Type")}


def inventory(path: Path) -> dict:
    matches = []
    hashed_total = 0
    total_files = 0
    unsafe = 0
    with zipfile.ZipFile(path) as z:
        for entry in z.infolist():
            if entry.is_dir():
                continue
            total_files += 1
            name = entry.filename.replace("\\", "/")
            if (name.startswith("/") or any(part in ("..", "") for part in name.split("/"))
                    or ":" in name):
                unsafe += 1
                continue
            lowered = name.lower()
            if not any(key in lowered for key in KEYS):
                continue
            item = {"path": name, "uncompressed": entry.file_size,
                    "compressed": entry.compress_size,
                    "crc32": f"{entry.CRC:08x}"}
            if (entry.file_size <= MAX_MEMBER_HASH and
                    hashed_total + entry.file_size <= MAX_HASHED_TOTAL):
                h = hashlib.sha256()
                size = 0
                with z.open(entry) as f:
                    while True:
                        chunk = f.read(512 * 1024)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > MAX_MEMBER_HASH:
                            raise ValueError("member over read budget")
                        h.update(chunk)
                if size != entry.file_size:
                    raise ValueError("unexpected member size")
                hashed_total += size
                item["sha256"] = h.hexdigest()
            matches.append(item)
    return {"zip_member_files": total_files, "unsafe_member_paths": unsafe,
            "matching_members": matches, "matching_members_count": len(matches),
            "individually_hashed_member_bytes": hashed_total}


def main() -> None:
    report = {"schema_version": "cy16-terasic-cd-probe-v1",
              "requested_url": URL, "binary_payload_published": False,
              "historical_binaries_executed": False}
    with tempfile.TemporaryDirectory(prefix="terasic-cd-") as folder:
        archive = Path(folder) / "original.zip"
        try:
            report.update(acquire(archive))
            report.update(inventory(archive))
            report["status"] = "zip_acquired_and_inventoried"
        except Exception as exc:
            report["status"] = "unavailable_or_invalid"
            report["failure_kind"] = type(exc).__name__
            report["failure_detail"] = str(exc)[:300]
    output = Path("harvest/metadata/terasic-cypress-cd.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("matching_members",)}, sort_keys=True))
    if report.get("matching_members"):
        print("Interesting ZIP members:")
        for item in report["matching_members"][:80]:
            print(f'  {item["path"]} [{item["uncompressed"]} bytes]')


if __name__ == "__main__":
    main()
