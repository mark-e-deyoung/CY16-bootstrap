from __future__ import annotations

import argparse
from pathlib import Path

from .common import le_to_word, read_bytes
from .isa import (
    RET_WORD, MODE_IMM, MODE_DIR_W, MODE_IND_R15, is_reg_mode, get_reg_from_mode,
    ALU_NAMES, OP_JMP_RET_PREFIX, OP_CALL_PREFIX, COND_ALWAYS
)


def disassemble(data: bytes, base: int = 0) -> list[str]:
    out: list[str] = []
    off = 0
    while off < len(data):
        addr = (base + off) & 0xFFFF
        if off + 1 >= len(data):
            out.append(f"{addr:04x}: .byte 0x{data[off]:02x}")
            break
        w = le_to_word(data, off)
        
        # Check for RET (specific form of JMP)
        if w == RET_WORD:
            out.append(f"{addr:04x}: {w:04x}          ret")
            off += 2
            continue
            
        opcode = (w >> 12)
        
        # Helper to get operand string and extension word
        def get_op_str(mode: int, ext_off: int, is_dst: bool = False) -> tuple[str, int]:
            if is_reg_mode(mode):
                return f"r{get_reg_from_mode(mode)}", 0
            if mode == MODE_IND_R15:
                return ("[--r15]" if is_dst else "[r15++]"), 0
            if mode == MODE_IMM:
                if ext_off + 1 < len(data):
                    val = le_to_word(data, ext_off)
                    return f"0x{val:04x}", 2
                return "??? (imm)", 0
            if mode == MODE_DIR_W:
                if ext_off + 1 < len(data):
                    val = le_to_word(data, ext_off)
                    return f"[0x{val:04x}]", 2
                return "??? ([addr])", 0
            return f"mode_{mode:02x}", 0

        # ALU operations
        if opcode in ALU_NAMES:
            op_name = ALU_NAMES[opcode]
            src_mode = (w >> 6) & 0x3F
            dst_mode = w & 0x3F
            
            s_str, s_len = get_op_str(src_mode, off + 2, is_dst=False)
            d_str, d_len = get_op_str(dst_mode, off + 2 + s_len, is_dst=True)
            
            words = [w]
            if s_len: words.append(le_to_word(data, off + 2))
            if d_len: words.append(le_to_word(data, off + 2 + s_len))
            
            words_hex = " ".join(f"{ww:04x}" for ww in words)
            out.append(f"{addr:04x}: {words_hex:<15}  {op_name} {d_str}, {s_str}")
            off += 2 + s_len + d_len
            continue

        # JMP/CALL
        if opcode == OP_JMP_RET_PREFIX or opcode == OP_CALL_PREFIX:
            op_name = 'jmp' if opcode == OP_JMP_RET_PREFIX else 'call'
            cond = (w >> 8) & 0xF
            is_abs = (w >> 7) & 1
            dst_mode = w & 0x3F
            
            if is_abs:
                d_str, d_len = get_op_str(dst_mode, off + 2, is_dst=True)
                words = [w]
                if d_len: words.append(le_to_word(data, off + 2))
                
                cond_str = f" if_{cond:x}" if cond != COND_ALWAYS else ""
                words_hex = " ".join(f"{ww:04x}" for ww in words)
                out.append(f"{addr:04x}: {words_hex:<15}  {op_name}{cond_str} {d_str}")
                off += 2 + d_len
                continue

        # Default
        out.append(f"{addr:04x}: {w:04x}          .word 0x{w:04x}")
        off += 2
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Bootstrap CY16 disassembler')
    ap.add_argument('input')
    ap.add_argument('--base', default='0')
    args = ap.parse_args(argv)
    base = int(args.base, 0)
    for line in disassemble(read_bytes(args.input), base=base):
        print(line)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
