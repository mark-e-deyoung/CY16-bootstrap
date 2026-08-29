"""Independent parser for historical Cypress QTASM listing files.

This module intentionally does not import the CY16 assembler, decoder, ISA tables,
or simulator. It treats a QTASM listing as external evidence and reconstructs the
bytes QTASM reported emitting.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Iterable


class QTASMListingError(ValueError):
    """Raised when a listing is ambiguous or internally inconsistent."""


@dataclass(frozen=True)
class ListingRecord:
    address: int
    data: bytes
    source_text: str
    listing_line: int


_TOKEN_RE = re.compile(r"(?:[0-9A-Fa-f]{2}|[0-9A-Fa-f]{4})(?=[ \t]|$)")
_PREFIX_RE = re.compile(
    r"^[ \t]{0,5}(?P<line>\d+)\s+(?P<addr>[0-9A-Fa-f]{4})\s+(?P<rest>.*)$"
)
_CONT_RE = re.compile(r"^[ \t]{6,}(?P<rest>.*)$")


def _token_bytes(token: str) -> bytes:
    if len(token) == 2:
        return bytes((int(token, 16),))
    if len(token) == 4:
        word = int(token, 16)
        return bytes((word & 0xFF, word >> 8))
    raise QTASMListingError(f"unsupported emitted token {token!r}")


def _parse_emitted_field(rest: str) -> tuple[bytes, str]:
    """Split QTASM emitted tokens from source text.

    Real QTASM 1.18x listings use single spaces between emitted tokens. Source text
    is usually padded into a later column, but some real records begin source text
    after only one space (for example a label such as ``@@:``). Therefore we parse
    tokens left-to-right and stop at the first non-token. A gap of two or more
    spaces also terminates emitted tokens; this prevents hexadecimal-looking source
    mnemonics such as ``db`` from being consumed as output bytes. Token matching
    also requires a whitespace/end boundary so source labels such as ``dbg_enable``
    cannot be mistaken for the emitted byte ``db``.
    """

    pos = 0
    out = bytearray()
    saw_token = False
    while pos < len(rest):
        if saw_token:
            ws = re.match(r"[ \t]+", rest[pos:])
            if not ws:
                break
            gap = ws.group(0)
            pos += len(gap)
            if len(gap.expandtabs(8)) >= 2:
                return bytes(out), rest[pos:].rstrip()
        match = _TOKEN_RE.match(rest, pos)
        if not match:
            break
        token = match.group(0)
        out.extend(_token_bytes(token))
        pos = match.end()
        saw_token = True

    if not saw_token:
        raise QTASMListingError("emitting record contains no byte/word tokens")
    return bytes(out), rest[pos:].lstrip().rstrip()


def _parse_continuation(rest: str) -> bytes | None:
    pos = 0
    out = bytearray()
    saw = False
    while pos < len(rest):
        ws = re.match(r"[ \t]*", rest[pos:])
        pos += len(ws.group(0))
        if pos >= len(rest):
            break
        match = _TOKEN_RE.match(rest, pos)
        if not match:
            return None
        out.extend(_token_bytes(match.group(0)))
        pos = match.end()
        saw = True
    return bytes(out) if saw else None


def parse_listing(text: str) -> list[ListingRecord]:
    """Parse emitted-byte records from a QTASM 1.18x-style listing."""

    records: list[ListingRecord] = []
    active_index: int | None = None

    for raw in text.splitlines():
        match = _PREFIX_RE.match(raw)
        if match:
            try:
                data, source = _parse_emitted_field(match.group("rest"))
            except QTASMListingError:
                active_index = None
                continue
            record = ListingRecord(
                address=int(match.group("addr"), 16),
                data=data,
                source_text=source,
                listing_line=int(match.group("line")),
            )
            records.append(record)
            active_index = len(records) - 1
            continue

        continuation = _CONT_RE.match(raw)
        if continuation and active_index is not None:
            data = _parse_continuation(continuation.group("rest"))
            if data is not None:
                previous = records[active_index]
                records[active_index] = ListingRecord(
                    address=previous.address,
                    data=previous.data + data,
                    source_text=previous.source_text,
                    listing_line=previous.listing_line,
                )
                continue

        active_index = None

    return records


def byte_map(records: Iterable[ListingRecord]) -> dict[int, int]:
    """Return address->byte evidence, rejecting contradictory overlaps."""

    memory: dict[int, int] = {}
    for record in records:
        for offset, value in enumerate(record.data):
            address = record.address + offset
            old = memory.get(address)
            if old is not None and old != value:
                raise QTASMListingError(
                    f"conflicting byte at 0x{address:04x}: 0x{old:02x} vs 0x{value:02x} "
                    f"(listing source line {record.listing_line})"
                )
            memory[address] = value
    return memory


def build_image(
    records: Iterable[ListingRecord],
    *,
    start: int | None = None,
    end: int | None = None,
    fill: int = 0,
) -> tuple[int, bytes]:
    """Reconstruct a contiguous image from listing evidence.

    ``end`` is exclusive. Missing addresses are filled explicitly (zero by
    default), which permits QTASM reservations to be reconstructed while keeping
    the fill policy visible to the caller.
    """

    if not 0 <= fill <= 0xFF:
        raise ValueError("fill must be a byte")

    memory = byte_map(records)
    if not memory:
        raise QTASMListingError("listing contains no emitted bytes")

    lo = min(memory) if start is None else start
    hi = max(memory) + 1 if end is None else end
    if hi < lo:
        raise ValueError("end precedes start")
    if any(address < lo or address >= hi for address in memory):
        raise QTASMListingError("emitted bytes fall outside requested image range")

    image = bytearray([fill]) * (hi - lo)
    for address, value in memory.items():
        image[address - lo] = value
    return lo, bytes(image)


def verify_image(
    image: bytes,
    *,
    expected_size: int | None = None,
    expected_sha256: str | None = None,
) -> None:
    """Fail closed if reconstructed bytes do not match pinned evidence metadata."""

    if expected_size is not None and len(image) != expected_size:
        raise QTASMListingError(
            f"image size mismatch: got {len(image)}, expected {expected_size}"
        )

    if expected_sha256 is not None:
        actual = hashlib.sha256(image).hexdigest()
        expected = expected_sha256.lower()
        if actual != expected:
            raise QTASMListingError(
                f"image SHA-256 mismatch: got {actual}, expected {expected}"
            )
