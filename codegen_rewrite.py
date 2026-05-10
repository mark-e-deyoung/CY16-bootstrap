import subprocess
import tempfile
import os

def compile_c(source: str) -> str:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write(source)
        tmp_c = f.name
    
    tmp_s = tmp_c[:-2] + '.s'
    subprocess.run(["./chibicc", tmp_c, "-S", "-o", tmp_s], check=True)
    
    with open(tmp_s) as f:
        asm = f.read()
        
    os.unlink(tmp_c)
    os.unlink(tmp_s)
    return asm
