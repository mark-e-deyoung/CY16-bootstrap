import subprocess
from cy16boot.asm import assemble
from cy16boot.sim import run

c_src = """
int g_i, g_sum, g_n;
int test_loop(void) {
    g_i = 0;
    g_sum = 0;
    while (g_i < g_n) {
        g_sum = g_sum + g_i;
        g_i = g_i + 1;
    }
    return g_sum;
}
"""
with open("test.c", "w") as f:
    f.write(c_src)

subprocess.run(["./chibicc", "test.c", "-S"])

with open("test.s") as f:
    asm = f.read()

full_asm = ".org 0x1000\n" + asm
image, _, _ = assemble(full_asm, base=0x1000)

from cy16boot.sim import CPU
cpu = CPU(pc=0x1000)
cpu.load(image, 0x1000)
_, _, syms = assemble(full_asm, base=0x1000)
cpu.writew(syms['_g_n'], 5)
cpu.regs[15] = 0xF000

while not cpu.halted and cpu.steps < 1000:
    cpu.step()
    
print("Sum is:", cpu.regs[0])
