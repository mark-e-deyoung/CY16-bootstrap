#!/usr/bin/env python3
"""Credentialless public-CI probe for historical CY16 vendor artifacts.

Unknown-license bytes may exist only in a temporary directory during the job.
Only metadata is written beneath harvest/metadata and eligible for artifact upload.
"""
from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
import mimetypes
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request

UA = "CY16-evidence-harvest/1.0 (+https://github.com/mark-e-deyoung/CY16-bootstrap)"
TIMEOUT = 30
MAX_BYTES = 128 * 1024 * 1024

TARGETS = [
    {
        "id": "xapp925",
        "kind": "direct",
        "url": "https://www.xilinx.com/bvdocs/appnotes/xapp925.zip",
        "wanted": "xapp925.zip",
    },
    {
        "id": "an15484-support",
        "kind": "landing",
        "url": "https://community.infineon.com/t5/USB-low-full-high-speed/Does-anybody-have-file-MSC-EEPROM-scan-LCP-v2-bin/td-p/63946",
        "wanted": "AN15484 - USB Flash Drive Controller Using SPI (EZ-Host USB Host).zip",
        "patterns": ["AN15484", "MSC_EEPROM_scan_LCP_v2", ".zip"],
    },
    {
        "id": "susb1",
        "kind": "landing",
        "url": "https://community.infineon.com/t5/Knowledge-Base-Articles/susb1-s-file/ta-p/249764",
        "wanted": "susb1.s",
        "patterns": ["susb1", ".s"],
    },
    {
        "id": "bios-release1",
        "kind": "landing",
        "url": "https://community.infineon.com/t5/Knowledge-Base-Articles/Software-USB-Stack-Implementation-For-EZ-Host-OTG/ta-p/250134",
        "wanted": "BIOS_Release1.zip",
        "patterns": ["BIOS_Release1", ".zip"],
    },
    {
        "id": "cy3663-rid14436",
        "kind": "direct",
        "url": "https://www.cypress.com/?rID=14436",
        "wanted": "CY3663 CD-ROM Image v1.0",
    },
]


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, "".join(self._text).strip()))
            self._href = None
            self._text = []


def request(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=TIMEOUT)


def get_small(url: str, limit: int = 8 * 1024 * 1024) -> tuple[bytes, str, dict[str, str]]:
    with request(url) as r:
        data = r.read(limit + 1)
        if len(data) > limit:
            raise RuntimeError(f"landing page exceeds {limit} bytes")
        return data, r.geturl(), dict(r.headers.items())


def candidate_links(base: str, html: bytes, patterns: list[str]) -> list[dict[str, str]]:
    parser = Links()
    parser.feed(html.decode("utf-8", errors="replace"))
    out = []
    needles = [p.lower() for p in patterns]
    for href, text in parser.links:
        absolute = urllib.parse.urljoin(base, href)
        hay = f"{absolute} {text}".lower()
        if any(n in hay for n in needles):
            out.append({"url": absolute, "text": text})
    # deterministic de-duplication
    seen = set()
    unique = []
    for item in out:
        key = item["url"]
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def download_metadata(url: str, tmp: Path) -> dict:
    h = hashlib.sha256()
    total = 0
    with request(url) as r, tmp.open("wb") as f:
        final_url = r.geturl()
        headers = dict(r.headers.items())
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_BYTES:
                raise RuntimeError(f"artifact exceeds {MAX_BYTES} bytes")
            h.update(chunk)
            f.write(chunk)
    guessed = mimetypes.guess_type(final_url)[0]
    file_type = subprocess.run(["file", "-b", str(tmp)], text=True, capture_output=True, check=True).stdout.strip()
    result = {
        "resolved_url": final_url,
        "bytes": total,
        "sha256": h.hexdigest(),
        "content_type": headers.get("Content-Type"),
        "guessed_mime": guessed,
        "file_type": file_type,
    }
    if "Zip archive" in file_type:
        p = subprocess.run(["unzip", "-Z1", str(tmp)], text=True, capture_output=True)
        result["archive_members"] = p.stdout.splitlines() if p.returncode == 0 else []
    elif "RAR archive" in file_type:
        p = subprocess.run(["7z", "l", "-ba", str(tmp)], text=True, capture_output=True)
        result["archive_listing"] = p.stdout.splitlines() if p.returncode == 0 else []
    return result


def main() -> None:
    meta_dir = Path("harvest/metadata")
    quarantine = Path("harvest/quarantine-bytes")
    meta_dir.mkdir(parents=True, exist_ok=True)
    quarantine.mkdir(parents=True, exist_ok=True)
    report = {"schema": 1, "targets": []}

    try:
        for target in TARGETS:
            entry = {"id": target["id"], "source": target["url"], "wanted": target["wanted"]}
            try:
                urls = []
                if target["kind"] == "landing":
                    html, resolved, headers = get_small(target["url"])
                    entry["landing_resolved_url"] = resolved
                    links = candidate_links(resolved, html, target.get("patterns", []))
                    entry["candidate_links"] = links
                    urls = [x["url"] for x in links]
                else:
                    urls = [target["url"]]

                probes = []
                for i, url in enumerate(urls[:12]):
                    path = quarantine / f"{target['id']}-{i}.bin"
                    try:
                        probes.append({"url": url, "ok": True, **download_metadata(url, path)})
                    except Exception as exc:
                        probes.append({"url": url, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
                    finally:
                        path.unlink(missing_ok=True)
                entry["probes"] = probes
                entry["status"] = "probed"
            except Exception as exc:
                entry["status"] = "error"
                entry["error"] = f"{type(exc).__name__}: {exc}"
            report["targets"].append(entry)
    finally:
        shutil.rmtree(quarantine, ignore_errors=True)

    (meta_dir / "vendor-probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    # Human-readable terse summary contains metadata only.
    lines = []
    for e in report["targets"]:
        lines.append(f"{e['id']}: {e.get('status')}")
        for p in e.get("probes", []):
            if p.get("ok"):
                lines.append(f"  {p['bytes']} bytes sha256={p['sha256']} {p['resolved_url']}")
            else:
                lines.append(f"  failed {p['url']}: {p.get('error')}")
    (meta_dir / "SUMMARY.txt").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
