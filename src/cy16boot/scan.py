from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from .common import le_to_word, read_bytes, word_to_le, write_bytes

SCAN_SIGNATURE = 0xC3B6
SCAN_OP_COPY = 0x00
SCAN_OP_JUMP = 0x04
SCAN_OP_CALL = 0x05
SCAN_OP_WRITE_CONFIG = 0x09
SCAN_OP_NAMES = {
    SCAN_OP_COPY: 'COPY',
    SCAN_OP_JUMP: 'JUMP',
    SCAN_OP_CALL: 'CALL',
    SCAN_OP_WRITE_CONFIG: 'WRITE_CONFIG',
}

# Known setup stub from Cypress scanwrap.c: mov [0xc03a], 0x23b3 ; ret
SETUP_STUB_WORDS = [0x07E7, 0x23B3, 0xC03A, 0xCF97]
SETUP_STUB_BYTES = b''.join(word_to_le(w) for w in SETUP_STUB_WORDS)


@dataclass(frozen=True)
class ScanRecord:
    offset: int
    length: int
    opcode: int
    address: int
    payload: bytes

    @property
    def size(self) -> int:
        return self.length + 5

    @property
    def name(self) -> str:
        return SCAN_OP_NAMES.get(self.opcode, f'OP_0x{self.opcode:02x}')


def make_record(opcode: int, address: int, payload: bytes = b'') -> bytes:
    # Cypress length counts address bytes plus payload, not signature/length/opcode.
    length = 2 + len(payload)
    return b''.join([
        word_to_le(SCAN_SIGNATURE),
        word_to_le(length),
        bytes([opcode & 0xFF]),
        word_to_le(address),
        payload,
    ])


def make_config_record(offset: int, value: int) -> bytes:
    """Create the documented SCAN opcode 0x09 configuration write.

    Unlike COPY/CALL/JUMP, this record contains a one-byte offset into
    control space 0xC000 followed by a little-endian 16-bit value.
    An external HPI loader must translate it to COMM_WRITE_CTRL_REG rather
    than issue a direct HPI write to 0xC000 + offset.
    """
    if not 0 <= offset <= 0xFF:
        raise ValueError('configuration offset must fit in one byte')
    if not 0 <= value <= 0xFFFF:
        raise ValueError('configuration value must fit in 16 bits')
    return b''.join([
        word_to_le(SCAN_SIGNATURE),
        word_to_le(3),
        bytes([SCAN_OP_WRITE_CONFIG, offset]),
        word_to_le(value),
    ])


def parse_scan(data: bytes) -> list[ScanRecord]:
    records: list[ScanRecord] = []
    pos = 0
    while pos + 1 < len(data):
        sig = le_to_word(data, pos)
        if sig == 0x0000:
            break
        if sig != SCAN_SIGNATURE:
            raise ValueError(f"bad SCAN signature at 0x{pos:04x}: 0x{sig:04x}")
        if pos + 5 > len(data):
            raise ValueError(f"truncated SCAN header at 0x{pos:04x}")

        length = le_to_word(data, pos + 2)
        opcode = data[pos + 4]
        body_start = pos + 5
        body_end = body_start + length
        if length == 0 or body_end > len(data):
            raise ValueError(f"bad SCAN length at 0x{pos:04x}: {length}")

        if opcode == SCAN_OP_WRITE_CONFIG:
            if length != 3:
                raise ValueError(
                    f"bad WRITE_CONFIG length at 0x{pos:04x}: {length}"
                )
            config_offset = data[body_start]
            address = 0xC000 | config_offset
            payload = data[body_start + 1:body_end]
        else:
            if length < 2:
                raise ValueError(f"record too short for address at 0x{pos:04x}: {length}")
            address = le_to_word(data, body_start)
            payload = data[body_start + 2:body_end]

        records.append(ScanRecord(pos, length, opcode, address, payload))
        pos += length + 5
    return records


def wrap_payload(payload: bytes, base_address: int, call_address: int | None = None, setup_address: int | None = None) -> bytes:
    if setup_address is None:
        setup_address = base_address
    if call_address is None:
        call_address = base_address
    # Keep Cypress-compatible alignment behavior explicit: a harmless COPY with 2 payload bytes.
    dummy = make_record(SCAN_OP_COPY, 0x00E0, b'\x00\x00')
    return b''.join([
        dummy,
        make_record(SCAN_OP_COPY, setup_address, SETUP_STUB_BYTES),
        make_record(SCAN_OP_CALL, setup_address),
        make_record(SCAN_OP_COPY, base_address, payload),
        make_record(SCAN_OP_CALL, call_address),
        b'\x00\x00',
    ])


def format_records(records: list[ScanRecord]) -> list[str]:
    lines: list[str] = []
    for r in records:
        first_words = []
        for i in range(0, min(len(r.payload), 16), 2):
            if i + 1 < len(r.payload):
                first_words.append(f"{le_to_word(r.payload, i):04x}")
            else:
                first_words.append(f"{r.payload[i]:02x}")
        lines.append(
            f"offset=0x{r.offset:04x} sig=0x{SCAN_SIGNATURE:04x} len=0x{r.length:04x} "
            f"op={r.name} addr=0x{r.address:04x} payload={len(r.payload)} "
            f"first_words={' '.join(first_words)}"
        )
    return lines


def decode_main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Decode Cypress CY16 SCAN records')
    ap.add_argument('input')
    args = ap.parse_args(argv)
    for line in format_records(parse_scan(read_bytes(args.input))):
        print(line)
    return 0


def wrap_main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Wrap a raw CY16 binary in SCAN records')
    ap.add_argument('input')
    ap.add_argument('output')
    ap.add_argument('base_address')
    ap.add_argument('call_address', nargs='?')
    args = ap.parse_args(argv)
    base = int(args.base_address, 0)
    call = int(args.call_address, 0) if args.call_address else None
    write_bytes(args.output, wrap_payload(read_bytes(args.input), base, call))
    return 0


if __name__ == '__main__':
    raise SystemExit(decode_main())
