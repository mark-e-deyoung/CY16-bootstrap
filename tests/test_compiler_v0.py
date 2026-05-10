import pytest
from cy16boot.asm import assemble
from cy16boot.sim import run
from cy16cc.codegen import compile_c

HEADER = "typedef unsigned short uint16_t;\ntypedef short int16_t;\ntypedef unsigned char uint8_t;\ntypedef char int8_t;\n"

def test_compiler_add():
    c_src = "uint16_t add(uint16_t a, uint16_t b) { return a + b; }"
    asm = compile_c(HEADER + c_src)
    # The new C backend emits prologue/epilogue.
    # Parameters are expected in r0, r1.
    image, assembled_words, symbols = assemble(asm)
    
    initial_regs = [0] * 16
    initial_regs[0] = 5
    initial_regs[1] = 7
    initial_regs[15] = 0xF000
    
    # We need to find the address of _add
    addr = symbols['_add']
    
    cpu, _ = run(image, 0, addr, 50, initial_regs=initial_regs)
    assert cpu.regs[0] == 12

def test_compiler_read_hwrev():
    c_src = "uint16_t read_hwrev(void) { return *(volatile uint16_t *)0xC004; }"
    asm = compile_c(HEADER + c_src)
    image, _, symbols = assemble(asm)
    
    from cy16boot.sim import CPU
    cpu = CPU(pc=symbols['_read_hwrev'])
    cpu.load(image, 0)
    cpu.writew(0xC004, 0x1234)
    cpu.regs[15] = 0xF000
    
    while not cpu.halted and cpu.steps < 50:
        cpu.step()
    assert cpu.regs[0] == 0x1234

def test_compiler_global_load_store():
    # The new C backend emits global definitions.
    c_src = """
    uint16_t g_var;
    uint16_t test_globals(void) {
        g_var = 0x55aa;
        return g_var;
    }
    """
    asm = compile_c(HEADER + c_src)
    # We don't need to manually append _g_var anymore.
    image, _, symbols = assemble(asm)
    
    cpu, _ = run(image, 0, symbols['_test_globals'], 100, initial_regs=[0]*16)
    assert cpu.readw(symbols['_g_var']) == 0x55AA
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
    image, _, symbols = assemble(asm)
    
    from cy16boot.sim import CPU
    cpu = CPU(pc=symbols['_test_loop'])
    cpu.load(image, 0)
    cpu.writew(symbols['_g_n'], 5)
    cpu.regs[15] = 0xF000
    
    while not cpu.halted and cpu.steps < 1000:
        cpu.step()
        
    assert cpu.readw(symbols['_g_sum']) == 10
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
    image, _, symbols = assemble(asm)
    
    initial_regs = [0] * 16
    initial_regs[15] = 0xF000
    
    cpu, _ = run(image, 0, symbols['_test_call'], 100, initial_regs=initial_regs)
    assert cpu.regs[0] == 10
