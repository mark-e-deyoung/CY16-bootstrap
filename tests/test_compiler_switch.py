from cy16boot.asm import assemble
from cy16boot.sim import run
from cy16cc.codegen import compile_c


HEADER = "typedef unsigned short uint16_t;\ntypedef short int16_t;\ntypedef unsigned char uint8_t;\ntypedef char int8_t;\n"


def run_switch(val: int) -> int:
    c_src = """
    uint16_t test_switch(uint16_t val) {
        uint16_t result = 0;
        switch (val) {
        case 1:
            result = 10;
            break;
        case 2:
            result = 20;
            break;
        case 3:
        case 4:
            result = 30;
            break;
        default:
            result = 100;
        }
        return result;
    }
    """
    asm = compile_c(HEADER + c_src)
    image, _, symbols = assemble(asm)
    regs = [0] * 16
    regs[0] = val
    regs[15] = 0xF000
    cpu, _ = run(image, 0, symbols["_test_switch"], 200, initial_regs=regs)
    return cpu.regs[0]


def test_compiler_switch_cases_and_default():
    for value, expected in [(1, 10), (2, 20), (3, 30), (4, 30), (5, 100)]:
        assert run_switch(value) == expected
