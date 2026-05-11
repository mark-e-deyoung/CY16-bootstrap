from __future__ import annotations

import argparse
from pathlib import Path

from .common import le_to_word, read_bytes
from .isa import (
    RET_WORD, MODE_IMM, MODE_DIR_W, MODE_IND_R15, is_reg_mode, get_reg_from_mode,
    ALU_NAMES, OP_JMP_RET_PREFIX, OP_CALL_PREFIX, COND_ALWAYS, COND_CODE_NAMES,
    is_ind_reg_mode, get_ind_reg_from_mode,
    SPECIAL_NAMES, OP_SPECIAL_PREFIX
)


def disassemble(data: bytes, base: int = 0, gnupro: bool = False) -> list[str]:
    out: list[str] = []
    off = 0
    def reg_name(reg: int) -> str:
        return f"%r{reg}" if gnupro else f"r{reg}"

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
                return reg_name(get_reg_from_mode(mode)), 0
            if mode == MODE_IND_R15:
                return (f"[--{reg_name(15)}]" if is_dst else f"[{reg_name(15)}++]"), 0
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
            if is_ind_reg_mode(mode):
                return f"[{reg_name(get_ind_reg_from_mode(mode))}]", 0
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

        # Special (shifts/addi/subi)
        if opcode == OP_SPECIAL_PREFIX:
            special_op = (w >> 9) & 0x7
            count = ((w >> 6) & 0x7) + 1
            dst_mode = w & 0x3F
            
            if special_op in SPECIAL_NAMES:
                op_name = SPECIAL_NAMES[special_op]
                d_str, d_len = get_op_str(dst_mode, off + 2, is_dst=True)
                
                words = [w]
                if d_len: words.append(le_to_word(data, off + 2))
                
                words_hex = " ".join(f"{ww:04x}" for ww in words)
                out.append(f"{addr:04x}: {words_hex:<15}  {op_name} {d_str}, {count}")
                off += 2 + d_len
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
                
                cond_name = COND_CODE_NAMES.get(cond, f"{cond:x}")
                cond_str = f" if_{cond_name}" if cond != COND_ALWAYS else ""
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
    ap.add_argument('--gnupro', action='store_true', help='print register names in GNUPro-compatible %%rN style')
    args = ap.parse_args(argv)
    base = int(args.base, 0)
    for line in disassemble(read_bytes(args.input), base=base, gnupro=args.gnupro):
        print(line)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
