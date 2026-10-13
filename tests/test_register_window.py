"""Independent contract tests for the opt-in CY16 register-window model."""
from cy16boot.register_window import RegisterWindow


def test_primary_register_mapping_and_memory_alias():
    model = RegisterWindow()
    model.write_register(14, 0xABCD)
    assert model.read_register(14) == 0xABCD
    assert model.memory[0x011C:0x011E] == bytes((0xCD, 0xAB))


def test_bank_swap_retains_each_windows_values():
    model = RegisterWindow()
    model.write_register(0, 0x1234)
    model.select_bank(0x0120)
    assert model.read_register(0) == 0
    model.write_register(0, 0x5678)
    model.select_bank(0x0100)
    assert model.read_register(0) == 0x1234
    model.select_bank(0x0120)
    assert model.read_register(0) == 0x5678


def test_low_five_bank_bits_do_not_change_mapping():
    model = RegisterWindow(regbank=0x011F)
    model.write_register(15, 0xCAFE)
    model.select_bank(0x0100)
    assert model.read_register(15) == 0xCAFE


def test_invalid_register_rejected():
    model = RegisterWindow()
    for reg in (-1, 16):
        try:
            model.read_register(reg)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid register {reg} accepted")
