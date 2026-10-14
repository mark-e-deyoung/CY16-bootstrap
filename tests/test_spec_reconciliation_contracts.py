"""Specification-derived, read-only CY16 architectural contract checks.

These tests verify the extracted address arithmetic and document current
simulator coverage gaps. They do not claim chip or simulator equivalence.
"""
from cy16boot.sim import CPU


def register_window_address(regbank: int, reg: int) -> int:
    assert 0 <= reg <= 15
    return (regbank & 0xFFE0) | (reg << 1)


def test_regbank_documented_example():
    assert register_window_address(0x0100, 14) == 0x011C


def test_regbank_ignores_low_five_bits():
    for bank in (0x0100, 0x0120, 0x0200):
        for reg in range(16):
            assert register_window_address(bank, reg) == register_window_address(bank | 0x1F, reg)


def test_regbank_windows_do_not_overlap():
    assert {register_window_address(0x0100, n) for n in range(16)}.isdisjoint(
        {register_window_address(0x0120, n) for n in range(16)}
    )


def test_ez_host_page_windows_are_distinct():
    first = range(0x8000, 0xA000)
    second = range(0xA000, 0xC000)
    assert len(first) == len(second) == 8192
    assert first.stop == second.start


def test_flat_simulator_is_not_register_window_aware():
    # Characterization test, not a conformance pass: current model keeps
    # register values separate from the architectural RAM-backed window.
    cpu = CPU()
    cpu.regs[14] = 0x1234
    assert cpu.readw(0x011C) == 0
    assert cpu.regs[14] == 0x1234
