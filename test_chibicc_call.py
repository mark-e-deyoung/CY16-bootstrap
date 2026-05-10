import subprocess

c_src = """
int double_it(int x) {
    return x + x;
}
int test_call(void) {
    return double_it(5);
}
"""
with open("test.c", "w") as f:
    f.write(c_src)

subprocess.run(["./chibicc", "test.c", "-S"])

with open("test.s") as f:
    asm = f.read()
print(asm)
