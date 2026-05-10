import pytest
from cy16boot.asm import assemble
from cy16boot.sim import run, main as sim_main

def test_sim_reg_init():
    initial = [0] * 16
    initial[0] = 0x1234
    initial[1] = 0x5678
    src = "mov r2, r0\nmov r3, r1\nret"
    image, _, _ = assemble(src)
    cpu, _ = run(image, 0, 0, 10, initial_regs=initial)
    assert cpu.regs[2] == 0x1234
    assert cpu.regs[3] == 0x5678

def test_sim_mov_forms():
    src = """
    mov r0, 0x1111
    mov [0x1000], r0
    mov r1, [0x1000]
    ret
    """
    image, _, _ = assemble(src)
    cpu, _ = run(image, 0, 0, 10)
    assert cpu.regs[0] == 0x1111
    assert cpu.readw(0x1000) == 0x1111
    assert cpu.regs[1] == 0x1111

def test_sim_mmio():
    # Use 0xC004 as an MMIO register
    src = "mov r0, [0xC004]\nret"
    image, _, _ = assemble(src)
    # Manual setup for MMIO-like behavior
    from cy16boot.sim import CPU
    cpu = CPU(pc=0x1000)
    cpu.load(image, 0x1000)
    cpu.writew(0xC004, 0xABCD)
    while not cpu.halted and cpu.steps < 10:
        cpu.step()
    assert cpu.regs[0] == 0xABCD

def test_sim_cli_regs(capsys, tmp_path):
    bin_file = tmp_path / "test.bin"
    src = "mov r2, r0\nret"
    image, _, _ = assemble(src)
    bin_file.write_bytes(image)
    
    # Test --reg and --dump-regs
    sim_main([str(bin_file), "--reg", "r0=0x1234", "--dump-regs"])
    captured = capsys.readouterr()
    assert "r00=0x1234" in captured.out
    assert "r02=0x1234" in captured.out
