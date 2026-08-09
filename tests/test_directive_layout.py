from __future__ import annotations

from pathlib import Path

import pytest

from cy16boot.asm import assemble, write_listing
from cy16boot.isa import RET_WORD


def word_addresses(source: str, base: int = 0) -> list[int]:
    _, words, _ = assemble(source, base=base)
    return [word.addr for word in words]


def test_one_byte_directive_places_next_label_and_word_at_plus_two() -> None:
    image, words, symbols = assemble(
        ".org 0x1000\n.byte 0xaa\nnext:\n    ret\n"
    )
    assert symbols["next"] == 0x1002
    assert [word.addr for word in words] == [0x1000, 0x1002]
    assert [word.value for word in words] == [0x00AA, RET_WORD]
    assert image == bytes((0xAA, 0x00, RET_WORD & 0xFF, RET_WORD >> 8))


@pytest.mark.parametrize(
    "directive, expected_prefix, expected_label",
    [
        ('.ascii "ABC"', b"ABC\x00", 0x1004),
        ('.asciz "AB"', b"AB\x00\x00", 0x1004),
        ('.space 3, 0x5a', b"\x5a\x5a\x5a\x00", 0x1004),
        ('.skip 1', b"\x00\x00", 0x1002),
    ],
)
def test_odd_byte_or_space_directives_use_same_padding_policy(
    directive: str,
    expected_prefix: bytes,
    expected_label: int,
) -> None:
    image, words, symbols = assemble(
        f".org 0x1000\n{directive}\nnext:\n    ret\n"
    )
    assert symbols["next"] == expected_label
    assert words[-1].addr == expected_label
    assert words[-1].value == RET_WORD
    assert image[: len(expected_prefix)] == expected_prefix


@pytest.mark.parametrize(
    "directive, expected_size",
    [
        ('.byte 0x11, 0x22', 2),
        ('.ascii "AB"', 2),
        ('.asciz "A"', 2),
        ('.space 4', 4),
        ('.skip 2, 0xff', 2),
    ],
)
def test_even_directive_sizes_are_unchanged(
    directive: str,
    expected_size: int,
) -> None:
    image, words, symbols = assemble(
        f".org 0x1000\n{directive}\nnext:\n    ret\n"
    )
    assert symbols["next"] == 0x1000 + expected_size
    assert words[-1].addr == 0x1000 + expected_size
    assert len(image) == expected_size + 2


def test_consecutive_odd_directives_do_not_overlap() -> None:
    image, words, symbols = assemble(
        ".org 0x1000\n"
        ".byte 0x11\n"
        ".byte 0x22\n"
        "next:\n"
        "    ret\n"
    )
    assert symbols["next"] == 0x1004
    assert [word.addr for word in words] == [0x1000, 0x1002, 0x1004]
    assert image == bytes(
        (0x11, 0x00, 0x22, 0x00, RET_WORD & 0xFF, RET_WORD >> 8)
    )


def test_absolute_jump_extension_uses_actual_padded_label() -> None:
    image, words, symbols = assemble(
        ".org 0x1000\n"
        "    jmp target\n"
        ".byte 0xaa\n"
        "target:\n"
        "    ret\n"
    )
    assert symbols["target"] == 0x1006
    assert words[1].addr == 0x1002
    assert words[1].value == 0x1006
    assert words[2].addr == 0x1004
    assert words[3].addr == 0x1006
    assert len(image) == 8


def test_listing_and_symbol_addresses_agree(tmp_path: Path) -> None:
    _, words, symbols = assemble(
        ".org 0x2000\n.ascii \"XYZ\"\nnext:\n    ret\n"
    )
    listing = tmp_path / "layout.lst"
    write_listing(listing, words)
    lines = listing.read_text(encoding="utf-8").splitlines()
    assert symbols["next"] == 0x2004
    assert lines[-1].startswith("2004:")
    assert word_addresses(
        ".org 0x2000\n.ascii \"XYZ\"\nnext:\n    ret\n"
    )[-1] == symbols["next"]
