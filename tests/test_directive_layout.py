from __future__ import annotations

from pathlib import Path

import pytest

from cy16boot.asm import assemble, write_listing
from cy16boot.common import Cy16Error
from cy16boot.isa import RET_WORD


def test_existing_flat_byte_directive_packing_is_preserved() -> None:
    image, words, symbols = assemble(
        ".org 0x1000\n"
        "label:\n"
        ".ascii \"A,\\n\"\n"
        ".asciz \"B\"\n"
        ".space 3, 0x55\n"
        ".skip 1\n"
    )
    assert symbols["label"] == 0x1000
    assert image == b"A,\nB\x00UUU\x00\x00"
    assert [word.addr for word in words] == [
        0x1000,
        0x1002,
        0x1003,
        0x1005,
        0x1007,
        0x1008,
    ]


@pytest.mark.parametrize(
    "statement",
    [
        "ret",
        ".word 0x1234",
        ".short 0x1234",
        "mov r0, 1",
        "addi r0, 1",
        "jmp 0x1000",
        "call 0x1000",
    ],
)
def test_word_statement_after_odd_byte_count_fails_closed(statement: str) -> None:
    with pytest.raises(Cy16Error, match="word statement starts at odd address"):
        assemble(f".org 0x1000\n.byte 0xaa\n{statement}\n")


def test_two_single_byte_directives_pack_and_restore_alignment() -> None:
    image, words, symbols = assemble(
        ".org 0x1000\n"
        ".byte 0x11\n"
        ".byte 0x22\n"
        "next:\n"
        "    ret\n"
    )
    assert symbols["next"] == 0x1002
    assert [word.addr for word in words] == [0x1000, 0x1001, 0x1002]
    assert image == bytes((0x11, 0x22, RET_WORD & 0xFF, RET_WORD >> 8))


def test_string_plus_explicit_pad_allows_following_instruction() -> None:
    image, words, symbols = assemble(
        ".org 0x1000\n"
        ".ascii \"ABC\"\n"
        ".byte 0\n"
        "next:\n"
        "    ret\n"
    )
    assert symbols["next"] == 0x1004
    assert words[-1].addr == 0x1004
    assert image == b"ABC\x00" + bytes((RET_WORD & 0xFF, RET_WORD >> 8))


def test_odd_data_label_remains_valid_when_no_word_statement_follows() -> None:
    image, words, symbols = assemble(
        ".org 0x2000\n"
        ".byte 0xaa\n"
        "odd_data:\n"
        ".byte 0xbb\n"
    )
    assert symbols["odd_data"] == 0x2001
    assert [word.addr for word in words] == [0x2000, 0x2001]
    assert image == b"\xaa\xbb\x00"


def test_absolute_target_uses_actual_flat_byte_layout() -> None:
    image, words, symbols = assemble(
        ".org 0x1000\n"
        "    jmp target\n"
        ".byte 0xaa, 0x00\n"
        "target:\n"
        "    ret\n"
    )
    assert symbols["target"] == 0x1006
    assert words[1].addr == 0x1002
    assert words[1].value == 0x1006
    assert words[2].addr == 0x1004
    assert words[3].addr == 0x1006
    assert len(image) == 8


def test_listing_and_symbol_addresses_agree_after_packed_bytes(tmp_path: Path) -> None:
    _, words, symbols = assemble(
        ".org 0x2000\n"
        ".byte 0x11\n"
        ".byte 0x22\n"
        "next:\n"
        "    ret\n"
    )
    listing = tmp_path / "layout.lst"
    write_listing(listing, words)
    lines = listing.read_text(encoding="utf-8").splitlines()
    assert symbols["next"] == 0x2002
    assert lines[-1].startswith("2002:")
