#!/usr/bin/env python3
"""Independent public CI oracle for Cypress GNUPro-produced CY16 SCAN arrays.

Inputs are fetched only by the surrounding pinned Git checkout. This tool
never runs vendor executables or claims access to the missing GNUPro toolchain.
Output contains metadata and cryptographic verification, not vendor bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


KNOWN = {
    "de1": {
        "asm": "727a124d9a1d0567b8923fc776c8b75e9a4f9c82",
        "header": "9beead959baa75c6693161262db3bdbc8733cfea",
        "recipe": "7f3d2a297cef3115204162fb30b08ee65c691718",
        "length": 202,
        "digest": "0c3359ddc5dff581295b4bcf107c5150b5301f75a051556e710306235c289b1b",
    },
    "de3": {
        "asm": "579fa2110f78fa8af47abcb6010a70577d3d8682",
        "header": "6fde198e698bfc6cb418af631ea2b138232f94bb",
        "recipe": "79a55cce5ea21df918a3ecf48f881f49d48404e7",
        "length": 174,
        "digest": "3e0063b15868d3e71e1c6ae6dda880266a6f8ea08fbb3d29f8b0075a66fb355d",
    },
}
ORIGIN = "HorseMa/uClinux-STM32"
COMMIT = "e0f4cc5029de32e09b17c5c5195c1ff686cb70d7"


def blob_id(payload: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\x00" + payload).hexdigest()


def expected_file(root: Path, filename: str, expected_sha1: str) -> bytes:
    blob = (root / filename).read_bytes()
    digest = blob_id(blob)
    if digest != expected_sha1:
        raise AssertionError(f"unexpected original Git blob for {filename}: {digest}")
    return blob


def inspect(root: Path) -> dict:
    observations = []
    for name, record in sorted(KNOWN.items()):
        asm = expected_file(root, name + "_bios.asm", record["asm"])
        header = expected_file(root, name + "_bios.h", record["header"])
        recipe = expected_file(root, "mk" + name + "bios.sh", record["recipe"])
        if b"GNU General Public License" not in asm:
            raise AssertionError(name + " source license notice changed")
        for command in (b"cy16-elf-as", b"cy16-elf-ld", b"cy16-elf-objcopy"):
            if command not in recipe:
                raise AssertionError(name + " historical assembler recipe changed")
        source = header.decode("utf-8")
        matcher = re.fullmatch(
            r"\s*static\s+unsigned\s+char\s+" + name +
            r"_bios\[(\d+)\]\s*=\s*\{([^}]*)\}\s*;\s*",
            source, re.DOTALL,
        )
        if not matcher:
            raise AssertionError(name + " generated header not understood")
        parts = re.findall(r"0x([0-9a-fA-F]{2})", matcher.group(2))
        if re.sub(r"0x[0-9a-fA-F]{2}|[\s,]", "", matcher.group(2)):
            raise AssertionError(name + " unexplained bytes in source")
        blob = bytes.fromhex("".join(parts))
        digest = hashlib.sha256(blob).hexdigest()
        if int(matcher.group(1)) != record["length"] or len(blob) != record["length"]:
            raise AssertionError(name + " byte count changed")
        if digest != record["digest"]:
            raise AssertionError(name + " historical image bytes differ")
        if blob[:4] != b"\xb6\xc3\x04\x00" or blob[9:11] != b"\xb6\xc3":
            raise AssertionError(name + " unexpected SCAN headers")
        observations.append({
            "id": name,
            "original_git_blobs_verified": True,
            "embedded_binary_size": len(blob),
            "embedded_binary_sha256": digest,
            "scan_header_observed": True,
            "independent_cy16_assembly_not_yet_run": True,
        })
    return {
        "schema_version": "cy16-public-oracle-v1",
        "origin": ORIGIN,
        "commit": COMMIT,
        "scope": "historical source/output identity, not recompilation",
        "historical_executables_run": False,
        "passed": True,
        "corpora": observations,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    report = inspect(args.source_root)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
