import subprocess
from cy16boot.asm import assemble
from cy16boot.sim import run

c_src = """
int g_var;
int test_globals(void) {
    g_var = 0x55aa;
    return g_var;
}
"""
with open("test.c", "w") as f:
    f.write(c_src)

subprocess.run(["./chibicc", "test.c", "-S"])

with open("test.s") as f:
    asm = f.read()
    
print(asm)
