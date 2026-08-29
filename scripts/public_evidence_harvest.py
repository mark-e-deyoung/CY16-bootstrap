#!/usr/bin/env python3
"""Credentialless public evidence harvester for CY16 research support.

Public-safe artifacts may be retained. Restricted/unknown inputs are analyzed
transiently and reduced to metadata only; their plaintext bytes are deleted.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import zipfile

ALLOW_HOSTS = {
    "raw.githubusercontent.com",
    "github.com",
    "community.infineon.com",
    "docs.amd.com",
    "www.infineon.com",
}
USER_AGENT = "CY16-public-evidence-harvester/1"


class HarvestError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_url(url: str) -> None:
    p = urlparse(url)
    if p.scheme != "https" or p.hostname not in ALLOW_HOSTS:
        raise HarvestError(f"URL not allowlisted: {url}")


def download(url: str, path: Path) -> tuple[str, str | None]:
    validate_url(url)
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as r, path.open("wb") as out:
        final_url = r.geturl()
        validate_url(final_url)
        while True:
            block = r.read(1024 * 1024)
            if not block:
                break
            out.write(block)
        return final_url, r.headers.get("Content-Type")


def identify(path: Path) -> dict:
    with path.open("rb") as f:
        head = f.read(16)
    if head.startswith(b"MZ"):
        kind = "pe"
    elif head.startswith(b"\x7fELF"):
        kind = "elf"
    elif head.startswith(b"%PDF-"):
        kind = "pdf"
    elif head.startswith(b"PK\x03\x04"):
        kind = "zip"
    else:
        kind = "binary"
    return {"kind": kind, "magic_hex": head.hex()}


def zip_inventory(path: Path) -> list[dict] | None:
    if not zipfile.is_zipfile(path):
        return None
    with zipfile.ZipFile(path) as zf:
        return [
            {
                "path": i.filename,
                "size": i.file_size,
                "compressed_size": i.compress_size,
                "crc32": f"{i.CRC:08x}",
            }
            for i in zf.infolist()
        ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan", type=Path)
    ap.add_argument("--out", type=Path, default=Path("harvest-output"))
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)
    safe_dir = args.out / "public-safe"
    safe_dir.mkdir(exist_ok=True)
    report = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "results": []}

    for item in plan["artifacts"]:
        url = item.get("url")
        if not url:
            report["results"].append({"id": item["id"], "status": item.get("mode", "no-url")})
            continue

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp = Path(tmp.name)
        try:
            final_url, content_type = download(url, temp)
            size = temp.stat().st_size
            if item.get("expected_size") is not None and size != item["expected_size"]:
                raise HarvestError(f"{item['id']} size mismatch: {size} != {item['expected_size']}")
            digest = sha256_file(temp)
            result = {
                "id": item["id"],
                "status": "observed",
                "requested_url": url,
                "final_url": final_url,
                "landing_page": item.get("landing_page"),
                "historical_url": item.get("historical_url"),
                "size": size,
                "sha256": digest,
                "content_type": content_type,
                "classification": item.get("classification"),
                "identification": identify(temp),
                "archive_inventory": zip_inventory(temp),
                "executed": False,
            }
            if item.get("classification") == "public-redistributable":
                dest = safe_dir / item["filename"]
                dest.write_bytes(temp.read_bytes())
                result["retained_publicly"] = True
                result["retained_path"] = str(dest)
            else:
                result["retained_publicly"] = False
            report["results"].append(result)
        finally:
            temp.unlink(missing_ok=True)

    (args.out / "harvest-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
