import subprocess
from cy16boot.asm import assemble
from cy16boot.sim import run

c_src = "int add(int a, int b) { return a + b; }"
with open("test.c", "w") as f:
    f.write(c_src)

subprocess.run(["./chibicc", "test.c", "-S"])

with open("test.s") as f:
    asm = f.read()

image, _, _ = assemble(asm)
initial_regs = [0] * 16
initial_regs[0] = 5
initial_regs[1] = 7
initial_regs[15] = 0xF000

cpu, _ = run(image, 0, 0, 50, initial_regs=initial_regs)
print(f"Result: {cpu.regs[0]}")
