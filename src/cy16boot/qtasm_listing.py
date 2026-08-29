"""Independent parser for historical Cypress QTASM listing files.

This module intentionally does not import the CY16 assembler, decoder, ISA tables,
or simulator.  It treats a QTASM listing as external evidence and reconstructs the
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


# QTASM 1.18x listing records look like:
#   53 0500 cf9f 06a2          jmp    init_code
#   43 04f4 00                 db     0
# Symbol/equate records use an eight-digit value rather than a four-digit address,
# so requiring exactly four address digits avoids treating them as emitted data.
_RECORD_RE = re.compile(
    r"^\s*(?P<line>\d+)\s+(?P<addr>[0-9A-Fa-f]{4})\s+"
    r"(?P<tokens>(?:[0-9A-Fa-f]{2}|[0-9A-Fa-f]{4})"
    r"(?:\s+(?:[0-9A-Fa-f]{2}|[0-9A-Fa-f]{4}))*)"
    r"(?:\s{2,}(?P<source>.*))?$"
)

# Long DB/DW strings can wrap onto continuation lines containing only emitted
# tokens.  We accept these only while a record is active.
_CONT_RE = re.compile(
    r"^\s{6,}(?P<tokens>(?:[0-9A-Fa-f]{2}|[0-9A-Fa-f]{4})"
    r"(?:\s+(?:[0-9A-Fa-f]{2}|[0-9A-Fa-f]{4}))*)\s*$"
)


def _tokens_to_bytes(tokens: str) -> bytes:
    out = bytearray()
    for token in tokens.split():
        if len(token) == 2:
            out.append(int(token, 16))
        elif len(token) == 4:
            word = int(token, 16)
            out.extend((word & 0xFF, word >> 8))
        else:  # defensive; regex should make this unreachable
            raise QTASMListingError(f"unsupported emitted token {token!r}")
    return bytes(out)


def parse_listing(text: str) -> list[ListingRecord]:
    """Parse emitted-byte records from a QTASM 1.18x-style listing.

    Non-emitting source/equate lines are ignored. Wrapped byte/word continuations
    are appended to the preceding emitting source record. Address regressions or
    conflicting overlaps are rejected by :func:`build_image`.
    """

    records: list[ListingRecord] = []
    active_index: int | None = None

    for physical_line, raw in enumerate(text.splitlines(), 1):
        match = _RECORD_RE.match(raw)
        if match:
            record = ListingRecord(
                address=int(match.group("addr"), 16),
                data=_tokens_to_bytes(match.group("tokens")),
                source_text=(match.group("source") or "").rstrip(),
                listing_line=int(match.group("line")),
            )
            records.append(record)
            active_index = len(records) - 1
            continue

        continuation = _CONT_RE.match(raw)
        if continuation and active_index is not None:
            previous = records[active_index]
            records[active_index] = ListingRecord(
                address=previous.address,
                data=previous.data + _tokens_to_bytes(continuation.group("tokens")),
                source_text=previous.source_text,
                listing_line=previous.listing_line,
            )
            continue

        # Any ordinary source/listing line terminates continuation eligibility.
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
    default), which permits QTASM ``dup`` reservations to be reconstructed while
    keeping the policy visible to the caller.
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
