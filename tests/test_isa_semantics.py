import pytest

from cy16boot.asm import assemble
from cy16boot.common import Cy16Error, le_to_word
from cy16boot.isa import SPECIAL_OPS, encode_special, make_reg_mode
from cy16boot.sim import CPU


def cpu_for(source: str, regs: list[int] | None = None) -> CPU:
    image, _, _ = assemble(source)
    cpu = CPU(pc=0)
    cpu.load(image, 0)
    if regs is not None:
        cpu.regs = list(regs)
    return cpu


def test_mov_preserves_all_flags():
    cpu = cpu_for("mov r0, 0x1234")
    cpu.fz = True
    cpu.fc = True
    cpu.fs = True
    cpu.fo = True

    cpu.step()

    assert cpu.regs[0] == 0x1234
    assert (cpu.fz, cpu.fc, cpu.fs, cpu.fo) == (True, True, True, True)


def test_addc_uses_carry_in_and_sets_arithmetic_flags():
    regs = [0] * 16
    regs[0] = 0xFFFF
    regs[1] = 0x0000
    cpu = cpu_for("addc r0, r1", regs)
    cpu.fc = True

    cpu.step()

    assert cpu.regs[0] == 0x0000
    assert cpu.fz
    assert cpu.fc
    assert not cpu.fs
    assert not cpu.fo


def test_subb_uses_borrow_in_and_sets_borrow_flag():
    regs = [0] * 16
    regs[0] = 0x0000
    regs[1] = 0x0000
    cpu = cpu_for("subb r0, r1", regs)
    cpu.fc = True

    cpu.step()

    assert cpu.regs[0] == 0xFFFF
    assert not cpu.fz
    assert cpu.fc
    assert cpu.fs
    assert not cpu.fo


def test_logical_operations_preserve_carry_and_overflow():
    regs = [0] * 16
    regs[0] = 0xF0F0
    regs[1] = 0x0FF0
    cpu = cpu_for("and r0, r1", regs)
    cpu.fc = True
    cpu.fo = True

    cpu.step()

    assert cpu.regs[0] == 0x00F0
    assert not cpu.fz
    assert not cpu.fs
    assert cpu.fc
    assert cpu.fo


@pytest.mark.parametrize(
    ("source", "initial", "expected", "carry"),
    [
        ("shr r0, 1", 0x8001, 0xC000, True),
        ("shl r0, 1", 0x8001, 0x0002, True),
        ("ror r0, 1", 0x0001, 0x8000, True),
        ("rol r0, 1", 0x8000, 0x0001, True),
    ],
)
def test_shift_and_rotate_semantics(source, initial, expected, carry):
    regs = [0] * 16
    regs[0] = initial
    cpu = cpu_for(source, regs)
    cpu.fo = True  # These operations do not document an overflow update.

    cpu.step()

    assert cpu.regs[0] == expected
    assert cpu.fc is carry
    assert cpu.fz is (expected == 0)
    assert cpu.fs is bool(expected & 0x8000)
    assert cpu.fo


@pytest.mark.parametrize("count", range(1, 9))
def test_small_immediate_field_stores_count_minus_one(count):
    image, _, _ = assemble(f"addi r0, {count}")
    encoded = le_to_word(image, 0)
    assert encoded == encode_special(SPECIAL_OPS["addi"], count, make_reg_mode(0))
    assert ((encoded >> 6) & 0x7) == count - 1


@pytest.mark.parametrize("count", [0, 9])
def test_small_immediate_out_of_range_is_rejected(count):
    with pytest.raises(Cy16Error):
        assemble(f"addi r0, {count}")


def test_addi_and_subi_preserve_carry_and_overflow():
    regs = [0] * 16
    regs[0] = 0xFFFF
    cpu = cpu_for("addi r0, 1", regs)
    cpu.fc = True
    cpu.fo = True
    cpu.step()
    assert cpu.regs[0] == 0
    assert cpu.fz
    assert cpu.fc
    assert cpu.fo

    regs[0] = 0
    cpu = cpu_for("subi r0, 1", regs)
    cpu.fc = True
    cpu.fo = True
    cpu.step()
    assert cpu.regs[0] == 0xFFFF
    assert cpu.fs
    assert cpu.fc
    assert cpu.fo


def test_r15_push_and_pop_word_behavior():
    regs = [0] * 16
    regs[0] = 0xA55A
    regs[15] = 0x0200
    cpu = cpu_for("mov [--r15], r0\nmov r1, [r15++]", regs)

    cpu.step()
    assert cpu.regs[15] == 0x01FE
    assert cpu.readw(0x01FE) == 0xA55A

    cpu.step()
    assert cpu.regs[1] == 0xA55A
    assert cpu.regs[15] == 0x0200
