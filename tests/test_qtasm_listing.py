import hashlib

import pytest

from cy16boot.qtasm_listing import (
    QTASMListingError,
    ListingRecord,
    build_image,
    parse_listing,
    verify_image,
)


def test_parses_qtasm_words_as_little_endian_bytes():
    listing = """QTASM rev 1.18x
  41 04f0 c3b6               dw     SCAN_SIGNATURE
  43 04f4 00                 db     0
  53 0500 cf9f 06a2          jmp    init_code
  34 050e cf97               ret
"""
    records = parse_listing(listing)

    assert records[0].address == 0x04F0
    assert records[0].data == bytes.fromhex("b6 c3")
    assert records[1].data == b"\x00"
    assert records[2].data == bytes.fromhex("9f cf a2 06")
    assert records[3].data == bytes.fromhex("97 cf")


def test_real_corpus_allows_one_space_before_nonhex_source_label():
    listing = " 136 11ea 57e7 003f 1126 @@: cmp    w[actual_lba_lw], FAT16_BOOT_BLOCK_LBA_LW\n"
    records = parse_listing(listing)
    assert len(records) == 1
    assert records[0].address == 0x11EA
    assert records[0].data == bytes.fromhex("e7 57 3f 00 26 11")
    assert records[0].source_text.startswith("@@: cmp")


def test_source_label_starting_with_hex_characters_is_not_emitted_data():
    listing = """
  29 0504                dbg_enable:
  30 0504 0017               push   r0
"""
    records = parse_listing(listing)
    assert len(records) == 1
    assert records[0].listing_line == 30
    assert records[0].data == bytes.fromhex("17 00")


def test_hexadecimal_looking_db_mnemonic_is_not_consumed_as_data():
    listing = "  43 04f4 00                 db     0\n"
    records = parse_listing(listing)
    assert records[0].data == b"\x00"
    assert records[0].source_text.startswith("db")


def test_ignores_equate_values_that_are_not_emitted_addresses():
    listing = """
  57           00000000  FILE_SIZE_LW equ 0x0000
  69           00000001  FW_REV equ 0x1
  30 0504 0017               push   r0
"""
    records = parse_listing(listing)
    assert len(records) == 1
    assert records[0].address == 0x0504


def test_appends_wrapped_db_and_dw_continuations():
    listing = """
 277 12b2 53 54 49 52 4c    db      'STIRLITZ   '
          49 54 5a 20 20
          20
 118 14be 004c 006f 0070    dw      'Loper OS'
          0065 0072 0020
          004f 0053
"""
    records = parse_listing(listing)

    assert records[0].data == b"STIRLITZ   "
    assert records[1].data == b"L\x00o\x00p\x00e\x00r\x00 \x00O\x00S\x00"


def test_build_image_fills_explicit_address_gaps():
    records = [
        ListingRecord(0x1000, b"\x01\x02", "first", 1),
        ListingRecord(0x1004, b"\x05", "second", 2),
    ]
    origin, image = build_image(records)
    assert origin == 0x1000
    assert image == bytes.fromhex("01 02 00 00 05")


def test_conflicting_overlap_fails_closed():
    records = [
        ListingRecord(0x1000, b"\x01\x02", "first", 1),
        ListingRecord(0x1001, b"\xff", "conflict", 2),
    ]
    with pytest.raises(QTASMListingError, match="conflicting byte"):
        build_image(records)


def test_identical_overlap_is_permitted_as_repeated_evidence():
    records = [
        ListingRecord(0x1000, b"\x01\x02", "first", 1),
        ListingRecord(0x1001, b"\x02", "same", 2),
    ]
    _, image = build_image(records)
    assert image == b"\x01\x02"


def test_requested_range_rejects_outside_emitted_bytes():
    records = [ListingRecord(0x1000, b"\x01", "x", 1)]
    with pytest.raises(QTASMListingError, match="outside requested"):
        build_image(records, start=0x1001, end=0x1002)


def test_verify_image_checks_size_and_hash():
    image = b"historical bytes"
    digest = hashlib.sha256(image).hexdigest()
    verify_image(image, expected_size=len(image), expected_sha256=digest.upper())

    with pytest.raises(QTASMListingError, match="size mismatch"):
        verify_image(image, expected_size=len(image) + 1)
    with pytest.raises(QTASMListingError, match="SHA-256 mismatch"):
        verify_image(image, expected_sha256="00" * 32)
