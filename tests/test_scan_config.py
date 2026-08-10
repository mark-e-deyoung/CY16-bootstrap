import pytest

from cy16boot.common import le_to_word
from cy16boot.scan import (
    SCAN_OP_WRITE_CONFIG,
    make_config_record,
    parse_scan,
)


# Infineon KBA example, shown in on-disk little-endian byte order.
KBA_WRITE_CONFIG = bytes.fromhex("b6 c3 03 00 09 3a 22 22")


def test_decode_documented_write_config_record():
    records = parse_scan(KBA_WRITE_CONFIG)
    assert len(records) == 1

    record = records[0]
    assert record.opcode == SCAN_OP_WRITE_CONFIG
    assert record.name == "WRITE_CONFIG"
    assert record.address == 0xC03A
    assert le_to_word(record.payload, 0) == 0x2222
    assert record.size == len(KBA_WRITE_CONFIG)


def test_encode_documented_write_config_record():
    assert make_config_record(0x3A, 0x2222) == KBA_WRITE_CONFIG


def test_write_config_rejects_bad_shape_and_values():
    with pytest.raises(ValueError):
        parse_scan(bytes.fromhex("b6 c3 02 00 09 3a 22"))
    with pytest.raises(ValueError):
        make_config_record(0x100, 0x2222)
    with pytest.raises(ValueError):
        make_config_record(0x3A, 0x10000)
