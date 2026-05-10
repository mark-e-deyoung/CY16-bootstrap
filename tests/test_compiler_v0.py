import pytest
from cy16boot.asm import assemble
from cy16boot.sim import run
from cy16cc.codegen import compile_c

HEADER = "typedef unsigned short uint16_t;\ntypedef short int16_t;\ntypedef unsigned char uint8_t;\ntypedef char int8_t;\n"

def test_compiler_add():
    c_src = "uint16_t add(uint16_t a, uint16_t b) { return a + b; }"
    asm = compile_c(HEADER + c_src)
    image, _, _ = assemble(asm)
    
    initial_regs = [0] * 16
    initial_regs[0] = 5
    initial_regs[1] = 7
    initial_regs[15] = 0xF000
    
    cpu, _ = run(image, 0, 0, 50, initial_regs=initial_regs)
    assert cpu.regs[0] == 12

def test_compiler_read_hwrev():
    c_src = "uint16_t read_hwrev(void) { return *(volatile uint16_t *)0xC004; }"
    asm = compile_c(HEADER + c_src)
    image, _, _ = assemble(asm)
    
    from cy16boot.sim import CPU
    cpu = CPU(pc=0)
    cpu.load(image, 0)
    cpu.writew(0xC004, 0x1234)
    cpu.regs[15] = 0xF000
    
    while not cpu.halted and cpu.steps < 50:
        cpu.step()
    assert cpu.regs[0] == 0x1234

def test_compiler_global_load_store():
    c_src = """
    uint16_t g_var;
    uint16_t test_globals(void) {
        g_var = 0x55aa;
        return g_var;
    }
    """
    asm = compile_c(HEADER + c_src)
    full_asm = ".org 0x1000\n" + asm + "\n.org 0x2000\n_g_var: .word 0\n"
    
    image, _, _ = assemble(full_asm, base=0x1000)
    cpu, _ = run(image, 0x1000, 0x1000, 100, initial_regs=[0]*16)
    assert cpu.readw(0x2000) == 0x55AA
    assert cpu.regs[0] == 0x55AA

def test_compiler_loop():
    c_src = """
    uint16_t g_i, g_sum, g_n;
    uint16_t test_loop(void) {
        g_i = 0;
        g_sum = 0;
        while (g_i < g_n) {
            g_sum = g_sum + g_i;
            g_i = g_i + 1;
        }
        return g_sum;
    }
    """
    asm = compile_c(HEADER + c_src)
    full_asm = ".org 0x1000\n" + asm + "\n.org 0x2000\n_g_i: .word 0\n_g_sum: .word 0\n_g_n: .word 0\n"
    image, _, _ = assemble(full_asm, base=0x1000)
    
    from cy16boot.sim import CPU
    cpu = CPU(pc=0x1000)
    cpu.load(image, 0x1000)
    cpu.writew(0x2004, 5) # g_n = 5
    cpu.regs[15] = 0xF000
    
    while not cpu.halted and cpu.steps < 1000:
        cpu.step()
        
    assert cpu.readw(0x2002) == 10 # g_sum
    assert cpu.regs[0] == 10

def test_compiler_call():
    c_src = """
    uint16_t double_it(uint16_t x) {
        return x + x;
    }
    uint16_t test_call(void) {
        return double_it(5);
    }
    """
    asm = compile_c(HEADER + c_src)
    image, _, _ = assemble(asm)
    
    initial_regs = [0] * 16
    initial_regs[15] = 0xF000
    
    # Entry point is test_call. We need to find its address or just put it first.
    # The codegen emits _double_it then _test_call.
    # Let's find _test_call address.
    _, _, symbols = assemble(asm)
    
    cpu, _ = run(image, 0, symbols['_test_call'], 100, initial_regs=initial_regs)
    assert cpu.regs[0] == 10
