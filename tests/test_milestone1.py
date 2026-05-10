import pytest
from cy16boot.asm import assemble
from cy16boot.dis import disassemble
from cy16boot.common import le_to_word

def words(data):
    return [le_to_word(data, i) for i in range(0, len(data), 2)]

def test_mov_reg_imm():
    src = "mov r0, 0x1234\nmov r15, 0xabcd"
    image, _, _ = assemble(src)
    # mov r0, 0x1234 -> 0000_011111_000000 = 0x07C0
    # mov r15, 0xabcd -> 0000_011111_001111 = 0x07CF
    assert words(image) == [0x07C0, 0x1234, 0x07CF, 0xABCD]

def test_mov_reg_dir():
    src = "mov r1, [0x1000]"
    image, _, _ = assemble(src)
    # mov r1, [0x1000] -> 0000_100111_000001 = 0x09C1
    assert words(image) == [0x09C1, 0x1000]

def test_mov_dir_reg():
    src = "mov [0x2000], r2"
    image, _, _ = assemble(src)
    # mov [0x2000], r2 -> 0000_000010_100111 = 0x00A7
    assert words(image) == [0x00A7, 0x2000]

def test_directives():
    src = """
    .org 0x100
    .equ VAL, 0x55
    .byte 0x11, 0x22
    .word 0x3344
    .short 0x7788
    .byte VAL
    """
    image, _, symbols = assemble(src)
    assert symbols['VAL'] == 0x55
    # .byte 0x11, 0x22 -> 0x2211 (LE)
    # .word 0x3344 -> 0x3344
    # .short 0x7788 -> 0x7788
    # .byte 0x55 -> 0x0055 (padded)
    assert words(image) == [0x2211, 0x3344, 0x7788, 0x0055]

def test_roundtrip():
    src = "mov r1, [0x1234]\nmov [0x5678], r1\nret"
    image, _, _ = assemble(src)
    lines = disassemble(image)
    # Extract the instruction part from disassembly lines
    # e.g. "0000: 09c1 1234      mov r1, [0x1234]"
    asm_output = "\n".join(l.split('  ')[-1].strip() for l in lines)
    assert "mov r1, [0x1234]" in asm_output
    assert "mov [0x5678], r1" in asm_output
    assert "ret" in asm_output
