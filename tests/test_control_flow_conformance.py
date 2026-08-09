import pytest

from cy16boot.asm import assemble
from cy16boot.common import Cy16Error, le_to_word
from cy16boot.dis import disassemble
from cy16boot.isa import (
    COND_ALWAYS,
    COND_Z,
    decode_jmp_rel_offset,
    encode_int,
    encode_jmp_rel,
    is_int_word,
)
from cy16boot.sim import CPU, run


def word_values(source: str, base: int = 0) -> list[int]:
    _, words, _ = assemble(source, base=base)
    return [word.value for word in words]


def test_relative_encoding_exact_boundaries():
    minus_64 = encode_jmp_rel(COND_ALWAYS, -64)
    plus_63 = encode_jmp_rel(COND_Z, 63)
    assert decode_jmp_rel_offset(minus_64) == -64
    assert decode_jmp_rel_offset(plus_63) == 63
    assert minus_64 & 0x7F == 0x40
    assert plus_63 & 0x7F == 0x3F


@pytest.mark.parametrize("offset", [-65, 64])
def test_relative_encoding_rejects_out_of_range(offset):
    with pytest.raises(ValueError, match="out of range"):
        encode_jmp_rel(COND_ALWAYS, offset)


def test_forced_short_assembler_boundaries():
    plus = word_values(".org 0x1000\n    jmp.s 0x1080\n")
    minus = word_values(".org 0x1080\n    jmp.s 0x1002\n")
    assert decode_jmp_rel_offset(plus[0]) == 63
    assert decode_jmp_rel_offset(minus[0]) == -64


@pytest.mark.parametrize(
    "source, expected",
    [
        (".org 0x1000\n    jmp.s 0x1082\n", "64"),
        (".org 0x1080\n    jmp.s 0x1000\n", "-65"),
    ],
)
def test_forced_short_assembler_rejects_boundary_overflow(source, expected):
    with pytest.raises(Cy16Error, match=expected):
        assemble(source)


def test_forced_short_rejects_odd_target():
    with pytest.raises(Cy16Error, match="not word aligned"):
        assemble(".org 0x1000\n    jmp.s 0x1003\n")


def test_unsuffixed_jump_relaxes_to_short_when_in_range():
    source = """
.org 0x1000
    jmp target
    mov r0, 1
target:
    ret
"""
    image, words, symbols = assemble(source)
    assert not (words[0].value & 0x80)
    assert decode_jmp_rel_offset(words[0].value) == 2
    assert symbols["target"] == 0x1006
    assert "jmp.s 0x1006" in disassemble(image, base=0x1000)[0]


def test_unsuffixed_jump_promotes_to_long_when_out_of_range():
    source = """
.org 0x1000
    jmp target
    .space 130
target:
    ret
"""
    image, words, symbols = assemble(source)
    assert words[0].value & 0x80
    assert words[1].value == symbols["target"]
    assert "jmp.l" in disassemble(image, base=0x1000)[0]


def test_explicit_historical_jump_suffixes():
    source = """
.org 0x1000
    jzs near
    jzl far
near:
    ret
far:
    ret
"""
    _, words, symbols = assemble(source)
    assert not (words[0].value & 0x80)
    assert words[1].value & 0x80
    assert words[2].value == symbols["far"]


def test_relative_jump_taken_and_not_taken_in_simulator():
    taken_source = """
.org 0x1000
    jmp.s target
    mov r0, 1
target:
    mov r0, 2
    ret
"""
    taken_image, _, _ = assemble(taken_source)
    regs = [0] * 16
    regs[15] = 0xF000
    cpu, trace = run(taken_image, 0x1000, 0x1000, 10, initial_regs=regs)
    assert cpu.regs[0] == 2
    assert cpu.halted
    assert "TAKEN" in trace[0]

    not_taken_source = """
.org 0x1000
    jz.s target
    mov r0, 1
    ret
target:
    mov r0, 2
    ret
"""
    not_taken_image, _, _ = assemble(not_taken_source)
    cpu, trace = run(not_taken_image, 0x1000, 0x1000, 10, initial_regs=regs)
    assert cpu.regs[0] == 1
    assert cpu.halted
    assert "not taken" in trace[0]


def test_backward_relative_jump_executes():
    source = """
.org 0x1000
    mov r0, 3
loop:
    subi r0, 1
    jnz.s loop
    ret
"""
    image, words, _ = assemble(source)
    branch_word = next(word.value for word in words if "jnz.s" in word.source)
    assert decode_jmp_rel_offset(branch_word) < 0
    regs = [0] * 16
    regs[15] = 0xF000
    cpu, _ = run(image, 0x1000, 0x1000, 20, initial_regs=regs)
    assert cpu.regs[0] == 0
    assert cpu.halted


def test_int_encoding_and_disassembly():
    assert encode_int(0) == 0xAF00
    assert encode_int(0x7F) == 0xAF7F
    assert is_int_word(0xAF00)
    assert is_int_word(0xAF7F)
    with pytest.raises(ValueError, match="out of range"):
        encode_int(0x80)

    image, _, _ = assemble(".org 0x1000\n    int 0x40\n")
    assert le_to_word(image, 0) == 0xAF40
    assert "int 0x40" in disassemble(image, base=0x1000)[0]


def test_int_pushes_return_loads_vector_and_ret_restores_pc():
    source = """
.org 0x1000
    int 0x40
    mov r0, 0x1234
    ret
.org 0x1100
handler:
    mov r1, 0x55aa
    ret
"""
    image, _, symbols = assemble(source)
    cpu = CPU(pc=0x1000)
    cpu.load(image, 0x1000)
    cpu.regs[15] = 0xF000
    cpu.writew(0x40 * 2, symbols["handler"])

    cpu.step()
    assert cpu.pc == symbols["handler"]
    assert cpu.regs[15] == 0xEFFE
    assert cpu.readw(0xEFFE) == 0x1002

    cpu.step()
    assert cpu.regs[1] == 0x55AA
    cpu.step()
    assert cpu.pc == 0x1002
    assert cpu.regs[15] == 0xF000

    cpu.step()
    assert cpu.regs[0] == 0x1234
    cpu.step()
    assert cpu.halted


def test_historical_macros_match_canonical_encodings_and_stack_behavior():
    pairs = [
        ("inc r0", "addi r0, 1"),
        ("dec r1", "subi r1, 1"),
        ("push r2", "mov [r15], r2"),
        ("pop r3", "mov r3, [r15]"),
    ]
    for macro, canonical in pairs:
        assert word_values(macro) == word_values(canonical)

    image, _, _ = assemble("push r0\npop r1\n")
    cpu = CPU(pc=0)
    cpu.load(image, 0)
    cpu.regs[0] = 0xCAFE
    cpu.regs[15] = 0xF000
    cpu.step()
    assert cpu.regs[15] == 0xEFFE
    assert cpu.readw(0xEFFE) == 0xCAFE
    cpu.step()
    assert cpu.regs[1] == 0xCAFE
    assert cpu.regs[15] == 0xF000
