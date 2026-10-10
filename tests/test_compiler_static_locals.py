"""Phase 9: CY16 C static-local persistence qualification.

Tests are deliberately end-to-end: chibicc CY16 backend -> assembler -> simulator.
No hardware, historical binary, or network access is required.
"""
from cy16boot.asm import assemble
from cy16boot.sim import run
from cy16cc.codegen import compile_c

HEADER = "typedef unsigned short uint16_t;\n"

def _execute(source, symbol, args=(), max_steps=500):
    asm = compile_c(HEADER + source)
    image, _, symbols = assemble(asm)
    regs = [0] * 16
    for index, arg in enumerate(args):
        regs[index] = arg
    regs[15] = 0xF000
    cpu, _ = run(image, 0, symbols[symbol], max_steps, initial_regs=regs)
    return cpu.regs[0], cpu

def test_static_local_initialized_and_reused_between_calls():
    source = """
    uint16_t bump(void) {
        static uint16_t counter = 7;
        counter = counter + 1;
        return counter;
    }
    uint16_t twice(void) {
        uint16_t first = bump();
        uint16_t second = bump();
        return first * 16 + second;
    }
    """
    value, _ = _execute(source, "_twice")
    assert value == 8 * 16 + 9

def test_static_local_separate_from_automatic_local():
    source = """
    uint16_t bump(uint16_t step) {
        static uint16_t saved = 2;
        uint16_t temporary = 100;
        saved = saved + step;
        temporary = temporary + saved;
        return temporary;
    }
    uint16_t twice(void) {
        uint16_t first = bump(3);
        uint16_t second = bump(4);
        return first + second;
    }
    """
    value, _ = _execute(source, "_twice")
    assert value == 105 + 109

def test_static_local_zero_initialization():
    source = """
    uint16_t bump(void) {
        static uint16_t count;
        count = count + 1;
        return count;
    }
    uint16_t twice(void) {
        uint16_t a = bump();
        uint16_t b = bump();
        return a * 16 + b;
    }
    """
    value, _ = _execute(source, "_twice")
    assert value == 0x12
