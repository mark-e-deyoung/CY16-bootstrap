"""Expected-failure tests: architectural behaviors absent from flat CPU.

These are intentionally strict specification-to-implementation probes.
They must not be counted as passing conformance evidence until the
architectural profile is implemented and the xfail markers removed.
"""
import pytest

from cy16boot.sim import CPU


@pytest.mark.xfail(strict=True, reason="flat CPU has no RAM-backed REGBANK register window")
def test_cpu_register_write_aliases_architectural_ram():
    cpu = CPU()
    cpu.regs[14] = 0xBEEF
    assert cpu.readw(0x011C) == 0xBEEF


@pytest.mark.xfail(strict=True, reason="flat CPU does not expose REGBANK MMIO at 0xC002")
def test_cpu_regbank_mmio_selects_new_window():
    cpu = CPU()
    cpu.writew(0x0100, 0x1234)
    cpu.writew(0x0120, 0x5678)
    cpu.writew(0xC002, 0x0120)
    assert cpu.regs[0] == 0x5678


@pytest.mark.xfail(strict=True, reason="flat CPU does not expose FLAGS MMIO at 0xC000")
def test_cpu_flags_readable_as_architectural_word():
    cpu = CPU()
    cpu.fz = True
    cpu.fc = True
    assert cpu.readw(0xC000) & 0x0003 == 0x0003
