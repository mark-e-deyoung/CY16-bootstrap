import pytest

from cy16boot.common import word_to_le
from cy16boot.scan import (
    SCAN_OP_CALL,
    SCAN_OP_COPY,
    SCAN_OP_JUMP,
    SCAN_SIGNATURE,
    make_record,
    parse_scan,
    wrap_payload,
)
from cy16boot.sim import CPU


def raw_record(opcode: int, body: bytes) -> bytes:
    return b"".join(
        [
            word_to_le(SCAN_SIGNATURE),
            word_to_le(len(body)),
            bytes([opcode]),
            body,
        ]
    )


def test_scan_accepts_exact_end_and_zero_padding():
    record = make_record(SCAN_OP_COPY, 0x1000, b"\x34\x12")
    assert len(parse_scan(record)) == 1
    assert len(parse_scan(record + b"\x00\x00\x00\x00")) == 1


def test_scan_rejects_truncated_and_nonzero_trailing_data():
    record = make_record(SCAN_OP_COPY, 0x1000, b"\x34\x12")
    with pytest.raises(ValueError, match="truncated SCAN terminator"):
        parse_scan(record + b"\x00")
    with pytest.raises(ValueError, match="non-zero data follows SCAN terminator"):
        parse_scan(record + b"\x00\x00\x01")


@pytest.mark.parametrize("opcode", [SCAN_OP_CALL, SCAN_OP_JUMP])
def test_known_control_records_require_exact_shape(opcode):
    malformed = raw_record(opcode, word_to_le(0x1000) + b"\xaa\xbb")
    with pytest.raises(ValueError, match="bad .* length"):
        parse_scan(malformed)
    with pytest.raises(ValueError, match="cannot contain payload"):
        make_record(opcode, 0x1000, b"\xaa\xbb")


def test_unknown_opcode_is_explicit_archaeology_policy():
    unknown = raw_record(0x7E, word_to_le(0x1234) + b"\xaa\xbb")
    with pytest.raises(ValueError, match="unknown SCAN opcode"):
        parse_scan(unknown)

    records = parse_scan(unknown, allow_unknown=True)
    assert len(records) == 1
    assert records[0].name == "OP_0x7e"
    assert records[0].address == 0x1234
    assert records[0].payload == b"\xaa\xbb"


@pytest.mark.parametrize(
    ("opcode", "address"),
    [(-1, 0x1000), (0x100, 0x1000), (SCAN_OP_COPY, -1), (SCAN_OP_COPY, 0x10000)],
)
def test_record_builder_rejects_out_of_range_fields(opcode, address):
    with pytest.raises(ValueError):
        make_record(opcode, address)


def test_record_builder_rejects_length_overflow_and_wrong_payload_type():
    with pytest.raises(ValueError, match="exceeds 16-bit"):
        make_record(SCAN_OP_COPY, 0x1000, b"\x00" * 0xFFFE)
    with pytest.raises(TypeError, match="payload must be bytes"):
        make_record(SCAN_OP_COPY, 0x1000, bytearray(b"\x00"))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"base_address": -1},
        {"base_address": 0x10000},
        {"base_address": 0x1000, "call_address": 0x10000},
        {"base_address": 0x1000, "setup_address": -1},
    ],
)
def test_wrap_payload_rejects_out_of_range_addresses(kwargs):
    with pytest.raises(ValueError):
        wrap_payload(b"\x00\x00", **kwargs)


def test_cpu_load_preserves_exact_64k_memory_boundary():
    cpu = CPU()
    cpu.load(b"\xaa", 0xFFFF)
    assert cpu.memory[0xFFFF] == 0xAA
    assert len(cpu.memory) == 0x10000

    with pytest.raises(ValueError, match="exceeds the 64 KiB"):
        cpu.load(b"\xaa\xbb", 0xFFFF)
    with pytest.raises(ValueError, match="base must be"):
        cpu.load(b"", -1)
    with pytest.raises(ValueError, match="base must be"):
        cpu.load(b"", 0x10000)

    assert len(cpu.memory) == 0x10000
