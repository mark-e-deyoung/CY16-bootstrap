import argparse
import sys
from pathlib import Path
from .codegen import compile_c

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cy16-cc")
    ap.add_argument("--version", action="store_true")
    ap.add_argument("-fsyntax-only", action="store_true")
    ap.add_argument("-S", action="store_true", help="Emit assembly")
    ap.add_argument("-o", "--output")
    ap.add_argument("input", nargs="?")
    args = ap.parse_args(argv)
    
    if args.version:
        print("cy16-cc version 0.1.0 (chibicc-derived)")
        return 0
    
    if not args.input:
        print("cy16-cc: error: no input files")
        return 1

    if args.fsyntax_only:
        print(f"Syntax check passed for {args.input} (stub)")
        return 0
        
    if args.S:
        source = Path(args.input).read_text(encoding='utf-8')
        # pycparser needs standard types defined
        header = "typedef unsigned short uint16_t;\ntypedef short int16_t;\ntypedef unsigned char uint8_t;\ntypedef char int8_t;\n"
        # Strip #include for now as we don't have a real preprocessor
        clean_source = "\n".join(line for line in source.splitlines() if not line.strip().startswith("#include"))
        asm = compile_c(header + clean_source)
        if args.output:
             Path(args.output).write_text(asm, encoding='utf-8')
        else:
             print(asm)
        return 0

    print(f"cy16-cc: error: compilation not yet implemented for {args.input} (use -S for assembly)")
    return 1

if __name__ == "__main__":
    sys.exit(main())
