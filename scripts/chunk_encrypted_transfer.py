#!/usr/bin/env python3
"""Split a verified encrypted vendor blob into individually bounded cloud artifacts.

No plaintext content, secret keys, or executables are handled here.
A full-file SHA-256 check precedes chunking; each part is independently hashed.
The original large encrypted file is removed after successful chunk validation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("harvest/encrypted")
SOURCE = ROOT / "terasic-de2-115-cypress-3.0.6.zip.enc"
META = ROOT / "terasic-encrypted-transfer.json"
REPORT = ROOT / "terasic-transfer-parts.json"
CHUNK_BYTES = 50_000_000


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    m = json.loads(META.read_text(encoding="utf-8"))
    if SOURCE.stat().st_size != m["ciphertext_bytes"]:
        raise ValueError("ciphertext size mismatch before split")
    if digest(SOURCE) != m["ciphertext_sha256"]:
        raise ValueError("ciphertext digest mismatch before split")
    if REPORT.exists():
        raise ValueError("existing split manifest; refusing overwrite")
    parts = []
    with SOURCE.open("rb") as source:
        for n in range(4):
            part = ROOT / f"part-{n:02d}.bin"
            if part.exists():
                raise ValueError(f"part exists: {part}")
            h = hashlib.sha256()
            total = 0
            with part.open("wb") as f:
                while total < CHUNK_BYTES:
                    chunk = source.read(min(1024 * 1024, CHUNK_BYTES - total))
                    if not chunk:
                        break
                    f.write(chunk)
                    h.update(chunk)
                    total += len(chunk)
            if not total:
                raise ValueError("unexpected empty part")
            parts.append({"index": n, "file": part.name,
                          "length": total, "sha256": h.hexdigest()})
        if source.read(1):
            raise ValueError("more than four chunks needed")
    if sum(x["length"] for x in parts) != m["ciphertext_bytes"]:
        raise ValueError("sum of part sizes differs from ciphertext")
    combined = hashlib.sha256()
    for part in parts:
        p = ROOT / part["file"]
        if p.stat().st_size != part["length"] or digest(p) != part["sha256"]:
            raise ValueError("split part identity changed")
        with p.open("rb") as f:
            for buf in iter(lambda: f.read(1024 * 1024), b""):
                combined.update(buf)
    if combined.hexdigest() != m["ciphertext_sha256"]:
        raise ValueError("parts fail to reconstitute ciphertext")
    output = {
        "schema_version": "cy16-encrypted-transfer-parts-v1",
        "original_archive_sha256": m["original_sha256"],
        "ciphertext_sha256": m["ciphertext_sha256"],
        "ciphertext_bytes": m["ciphertext_bytes"],
        "parts": parts,
        "plaintext_published": False,
        "reassembly_sha256_passed": True,
    }
    REPORT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SOURCE.unlink()
    print(json.dumps({"parts": parts, "ciphertext_sha256": m["ciphertext_sha256"],
                      "full_ciphertext_removed_from_public_artifact_staging": True},
                     sort_keys=True))


if __name__ == "__main__":
    main()
