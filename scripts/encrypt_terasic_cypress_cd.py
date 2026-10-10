#!/usr/bin/env python3
"""Fetch an exact vendor archive and encrypt it for private archival transport.

Public GHA only receives the *recipient public key*. No private secrets or
vendor plaintext are uploaded to Actions artifacts. All plaintext is disposed
inside a TemporaryDirectory before the job uploads ciphertext and metadata.
"""
from __future__ import annotations

import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlparse
from urllib.request import Request, urlopen

URL = ("https://download.terasic.com/downloads/cd-rom/de2-115/"
       "CD-ROM_Cypress_USB/DE2-115_v.3.0.6_SystemCD.zip")
EXPECTED_SHA256 = "d02d98f57eebe56bac71e0f8c382f50330f34834a60a6db7eb5bff80cd8954e5"
EXPECTED_SIZE = 194204218
RECIPIENT_PUBLIC_KEY_B64 = "8eQMYX2pKobLSCng4W6DVhj6xs03sCJpXS9CURPirEk="
HKDF_INFO = b"cy16-terasic-archive-transfer-v1"
OUT = Path("harvest/encrypted/terasic-de2-115-cypress-3.0.6.zip.enc")


def is_allowed(url: str) -> bool:
    p = urlparse(url)
    return p.scheme == "https" and p.hostname == "download.terasic.com"


def fetch(original: Path) -> str:
    if not is_allowed(URL):
        raise ValueError("target is not allowlisted")
    count = 0
    h = hashlib.sha256()
    req = Request(URL, headers={"User-Agent": "CY16-evidence-transport/1"})
    with urlopen(req, timeout=90) as response, original.open("wb") as dest:
        if not is_allowed(response.geturl()):
            raise ValueError("redirect out of approved host")
        header = response.headers.get("Content-Length")
        if header is not None and int(header) != EXPECTED_SIZE:
            raise ValueError("server Content-Length mismatch")
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            count += len(chunk)
            if count > EXPECTED_SIZE:
                raise ValueError("archive exceeded pinned size")
            dest.write(chunk)
            h.update(chunk)
    if count != EXPECTED_SIZE or h.hexdigest() != EXPECTED_SHA256:
        raise ValueError("download did not match previously verified archive")
    return h.hexdigest()


def encrypt(original: Path, ciphertext: Path) -> dict:
    recipient = X25519PublicKey.from_public_bytes(base64.b64decode(RECIPIENT_PUBLIC_KEY_B64))
    ephemeral = X25519PrivateKey.generate()
    salt, nonce = os.urandom(32), os.urandom(12)
    derived_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt,
                       info=HKDF_INFO).derive(ephemeral.exchange(recipient))
    aad_fields = {
        "schema_version": "cy16-encrypted-transfer-v1",
        "source_url": URL,
        "original_sha256": EXPECTED_SHA256,
        "original_size": EXPECTED_SIZE,
    }
    aad = json.dumps(aad_fields, sort_keys=True, separators=(",", ":")).encode("utf-8")
    encryptor = Cipher(algorithms.AES(derived_key), modes.GCM(nonce)).encryptor()
    encryptor.authenticate_additional_data(aad)
    ciphertext.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with original.open("rb") as source, ciphertext.open("wb") as out:
        while True:
            buf = source.read(1024 * 1024)
            if not buf:
                break
            encrypted = encryptor.update(buf)
            out.write(encrypted)
            h.update(encrypted)
        last = encryptor.finalize()
        out.write(last)
        h.update(last)
    if ciphertext.stat().st_size != EXPECTED_SIZE:
        raise ValueError("unexpected ciphertext length")
    report = {
        **aad_fields,
        "ephemeral_public_key_b64": base64.b64encode(
            ephemeral.public_key().public_bytes(
                serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        ).decode("ascii"),
        "recipient_public_key_b64": RECIPIENT_PUBLIC_KEY_B64,
        "hkdf": "X25519 + HKDF-SHA256; info cy16-terasic-archive-transfer-v1",
        "cipher": "AES-256-GCM",
        "salt_b64": base64.b64encode(salt).decode("ascii"),
        "nonce_b64": base64.b64encode(nonce).decode("ascii"),
        "gcm_tag_b64": base64.b64encode(encryptor.tag).decode("ascii"),
        "ciphertext_sha256": h.hexdigest(),
        "ciphertext_bytes": ciphertext.stat().st_size,
        "executed_historical_binaries": False,
        "plaintext_uploaded_to_public_artifact": False,
    }
    return report


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="cy16-vendor-transit-") as tmp:
        original = Path(tmp) / "original.zip"
        fetch(original)
        report = encrypt(original, OUT)
    # TemporaryDirectory is disposed before metadata or ciphertext upload.
    (OUT.parent / "terasic-encrypted-transfer.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"schema": report["schema_version"],
                      "source_sha256": report["original_sha256"],
                      "ciphertext_sha256": report["ciphertext_sha256"],
                      "ciphertext_bytes": report["ciphertext_bytes"],
                      "cipher": report["cipher"],
                      "plaintext_published": False}, sort_keys=True))


if __name__ == "__main__":
    main()
