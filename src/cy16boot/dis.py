from __future__ import annotations

import argparse
from pathlib import Path

from .common import le_to_word, read_bytes
from .isa import (
    RET_WORD, MODE_IMM, MODE_DIR_W, MODE_IND_R15, is_reg_mode, get_reg_from_mode,
    ALU_NAMES, OP_JMP_RET_PREFIX, OP_CALL_PREFIX, COND_ALWAYS, COND_CODE_NAMES,
    is_ind_reg_mode, get_ind_reg_from_mode,
    SPECIAL_NAMES, OP_SPECIAL_PREFIX,
    decode_jmp_rel_offset, is_int_word,
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

        if w == RET_WORD:
            out.append(f"{addr:04x}: {w:04x}          ret")
            off += 2
            continue

        if is_int_word(w):
            vector = w & 0x7F
            out.append(f"{addr:04x}: {w:04x}          int 0x{vector:02x}")
            off += 2
            continue

        opcode = w >> 12

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

        if opcode in ALU_NAMES:
            op_name = ALU_NAMES[opcode]
            src_mode = (w >> 6) & 0x3F
            dst_mode = w & 0x3F

            s_str, s_len = get_op_str(src_mode, off + 2, is_dst=False)
            d_str, d_len = get_op_str(dst_mode, off + 2 + s_len, is_dst=True)

            words = [w]
            if s_len:
                words.append(le_to_word(data, off + 2))
            if d_len:
                words.append(le_to_word(data, off + 2 + s_len))

            words_hex = " ".join(f"{word:04x}" for word in words)
            out.append(f"{addr:04x}: {words_hex:<15}  {op_name} {d_str}, {s_str}")
            off += 2 + s_len + d_len
            continue

        if opcode == OP_SPECIAL_PREFIX:
            special_op = (w >> 9) & 0x7
            count = ((w >> 6) & 0x7) + 1
            dst_mode = w & 0x3F

            if special_op in SPECIAL_NAMES:
                op_name = SPECIAL_NAMES[special_op]
                d_str, d_len = get_op_str(dst_mode, off + 2, is_dst=True)

                words = [w]
                if d_len:
                    words.append(le_to_word(data, off + 2))

                words_hex = " ".join(f"{word:04x}" for word in words)
                out.append(f"{addr:04x}: {words_hex:<15}  {op_name} {d_str}, {count}")
                off += 2 + d_len
                continue

        if opcode == OP_JMP_RET_PREFIX:
            cond = (w >> 8) & 0xF
            is_abs = (w >> 7) & 1
            cond_name = COND_CODE_NAMES.get(cond, f"{cond:x}")

            if not is_abs:
                offset_words = decode_jmp_rel_offset(w)
                target = (addr + 2 + offset_words * 2) & 0xFFFF
                mnemonic = "jmp.s" if cond == COND_ALWAYS else f"j{cond_name}.s"
                out.append(f"{addr:04x}: {w:04x}          {mnemonic} 0x{target:04x}")
                off += 2
                continue

            dst_mode = w & 0x3F
            d_str, d_len = get_op_str(dst_mode, off + 2, is_dst=True)
            words = [w]
            if d_len:
                words.append(le_to_word(data, off + 2))
            words_hex = " ".join(f"{word:04x}" for word in words)
            mnemonic = "jmp.l" if cond == COND_ALWAYS else f"j{cond_name}.l"
            out.append(f"{addr:04x}: {words_hex:<15}  {mnemonic} {d_str}")
            off += 2 + d_len
            continue

        if opcode == OP_CALL_PREFIX:
            cond = (w >> 8) & 0xF
            is_abs = (w >> 7) & 1
            if is_abs:
                dst_mode = w & 0x3F
                d_str, d_len = get_op_str(dst_mode, off + 2, is_dst=True)
                words = [w]
                if d_len:
                    words.append(le_to_word(data, off + 2))
                words_hex = " ".join(f"{word:04x}" for word in words)
                cond_name = COND_CODE_NAMES.get(cond, f"{cond:x}")
                mnemonic = "call" if cond == COND_ALWAYS else f"c{cond_name}"
                out.append(f"{addr:04x}: {words_hex:<15}  {mnemonic} {d_str}")
                off += 2 + d_len
                continue

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
