from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re

from .common import Cy16Error, Word, eval_expr, split_operands, strip_comment, u16, word_to_le, write_bytes
from .isa import (
    RET_WORD, MODE_IMM, MODE_DIR_W, MODE_IND_R15, encode_alu, make_reg_mode,
    OP_MOV, OP_ADD, OP_ADDC, OP_SUB, OP_SUBB, OP_CMP, OP_AND, OP_TEST, OP_OR, OP_XOR,
    COND_ALWAYS, encode_jmp_abs, encode_call_abs, ALU_OPS,
    make_ind_reg_mode, COND_NAMES, OP_JMP_RET_PREFIX, OP_CALL_PREFIX,
    SPECIAL_OPS, encode_special
)

@dataclass
class Line:
    number: int
    text: str
    label: str | None = None
    body: str = ""
    addr: int | None = None


def parse_source(source: str) -> list[Line]:
    lines: list[Line] = []
    for idx, raw in enumerate(source.splitlines(), start=1):
        text = strip_comment(raw)
        if not text:
            continue
        label = None
        body = text
        if ':' in text:
            maybe_label, rest = text.split(':', 1)
            if re.fullmatch(r'[A-Za-z_.$][A-Za-z0-9_.$]*', maybe_label.strip()):
                label = maybe_label.strip()
                body = rest.strip()
        lines.append(Line(idx, raw.rstrip('\n'), label=label, body=body))
    return lines


def parse_operand(op: str) -> tuple[int, str | None]:
    """Returns (mode, expr_to_evaluate_for_extension_word_or_None)."""
    low = op.lower().strip()
    if low.startswith('r') and low[1:].isdigit():
        reg = int(low[1:])
        if 0 <= reg <= 15:
            return make_reg_mode(reg), None
    if low == '[r15++]' or low == '[--r15]':
        return MODE_IND_R15, None
    if op.startswith('[') and op.endswith(']'):
        inner = op[1:-1].strip().lower()
        if inner.startswith('r') and inner[1:].isdigit():
            reg = int(inner[1:])
            if 8 <= reg <= 15:
                return make_ind_reg_mode(reg), None
        return MODE_DIR_W, op[1:-1]
    # Otherwise, treat as immediate
    return MODE_IMM, op


def estimate_words(body: str) -> int:
    if not body:
        return 0
    low = body.strip().lower()
    if low.startswith(('.org', '.equ', '.global', '.globl', '.section', '.include')):
        return 0
    if low.startswith(('.short', '.word')):
        return len(split_operands(body.split(None, 1)[1] if len(body.split(None, 1)) > 1 else ''))
    if low.startswith('.byte'):
        n = len(split_operands(body.split(None, 1)[1] if len(body.split(None, 1)) > 1 else ''))
        return (n + 1) // 2
    if low == 'ret':
        return 1
    
    op_parts = low.split(None, 1)
    op_name = op_parts[0]
    if op_name in ALU_OPS:
        ops = split_operands(op_parts[1].strip() if len(op_parts) > 1 else "")
        if len(ops) == 2:
            src_mode, src_ext = parse_operand(ops[1])
            dst_mode, dst_ext = parse_operand(ops[0])
            return 1 + (1 if src_ext is not None else 0) + (1 if dst_ext is not None else 0)
    
    if op_name in SPECIAL_OPS:
        ops = split_operands(op_parts[1].strip() if len(op_parts) > 1 else "")
        if len(ops) == 2:
            mode, ext = parse_operand(ops[0])
            return 1 + (1 if ext is not None else 0)

    if op_name == 'jmp' or op_name == 'call' or (op_name.startswith(('j', 'c')) and op_name[1:] in COND_NAMES):
        target = op_parts[1].strip() if len(op_parts) > 1 else ""
        mode, ext = parse_operand(target)
        return 1 + (1 if ext is not None else 0)

    raise Cy16Error(f"cannot estimate size for unsupported statement: {body}")


def first_pass(lines: list[Line], base: int) -> dict[str, int]:
    symbols: dict[str, int] = {}
    pc = base
    for line in lines:
        body = line.body.strip()
        low = body.lower()
        if low.startswith('.org'):
            pc = eval_expr(body.split(None, 1)[1], symbols, pc) & 0xFFFF
        line.addr = pc
        if line.label:
            if line.label in symbols:
                raise Cy16Error(f"line {line.number}: duplicate label {line.label}")
            symbols[line.label] = pc
        if not body:
            continue
        if low.startswith('.equ'):
            rest = body.split(None, 1)[1]
            name, expr = split_operands(rest)
            symbols[name] = eval_expr(expr, symbols, pc) & 0xFFFF
        pc += estimate_words(body) * 2
        pc &= 0xFFFF
    return symbols


def assemble(source: str, base: int = 0) -> tuple[bytes, list[Word], dict[str, int]]:
    lines = parse_source(source)
    symbols = first_pass(lines, base)
    pc = base
    words: list[Word] = []
    for line in lines:
        body = line.body.strip()
        if not body:
            continue
        low = body.lower()
        if low.startswith('.org'):
            pc = eval_expr(body.split(None, 1)[1], symbols, pc) & 0xFFFF
            continue
        if low.startswith(('.equ', '.global', '.globl', '.section', '.include')):
            continue
        if low.startswith(('.short', '.word')):
            rest = body.split(None, 1)[1]
            for expr in split_operands(rest):
                words.append(Word(pc, u16(eval_expr(expr, symbols, pc)), line.text))
                pc = (pc + 2) & 0xFFFF
            continue
        if low.startswith('.byte'):
            rest = body.split(None, 1)[1]
            vals = [eval_expr(expr, symbols, pc) & 0xFF for expr in split_operands(rest)]
            if len(vals) & 1:
                vals.append(0)
            for i in range(0, len(vals), 2):
                words.append(Word(pc, vals[i] | (vals[i+1] << 8), line.text))
                pc = (pc + 2) & 0xFFFF
            continue
        if low == 'ret':
            words.append(Word(pc, RET_WORD, line.text))
            pc = (pc + 2) & 0xFFFF
            continue
        
        op_parts = line.body.strip().split(None, 1)
        op_name = op_parts[0].lower()
        if op_name in ALU_OPS:
            ops = split_operands(op_parts[1].strip() if len(op_parts) > 1 else "")
            if len(ops) != 2:
                raise Cy16Error(f"line {line.number}: {op_name} requires two operands")
            dst, src = ops
            src_mode, src_ext = parse_operand(src)
            dst_mode, dst_ext = parse_operand(dst)
            
            enc = encode_alu(ALU_OPS[op_name], src_mode, dst_mode)
            words.append(Word(pc, enc, line.text))
            pc = (pc + 2) & 0xFFFF
            
            if src_ext is not None:
                val = eval_expr(src_ext, symbols, pc) & 0xFFFF
                words.append(Word(pc, val, line.text))
                pc = (pc + 2) & 0xFFFF
            if dst_ext is not None:
                val = eval_expr(dst_ext, symbols, pc) & 0xFFFF
                words.append(Word(pc, val, line.text))
                pc = (pc + 2) & 0xFFFF
            continue
            
        if op_name in SPECIAL_OPS:
            ops = split_operands(op_parts[1].strip() if len(op_parts) > 1 else "")
            if len(ops) != 2:
                raise Cy16Error(f"line {line.number}: {op_name} requires two operands")
            dst, count_expr = ops
            dst_mode, dst_ext = parse_operand(dst)
            count = eval_expr(count_expr, symbols, pc)
            if not (1 <= count <= 8):
                raise Cy16Error(f"line {line.number}: shift/addi count must be 1-8")
            
            enc = encode_special(SPECIAL_OPS[op_name], count, dst_mode)
            words.append(Word(pc, enc, line.text))
            pc = (pc + 2) & 0xFFFF
            if dst_ext is not None:
                val = eval_expr(dst_ext, symbols, pc) & 0xFFFF
                words.append(Word(pc, val, line.text))
                pc = (pc + 2) & 0xFFFF
            continue

        if op_name == 'jmp' or op_name == 'call' or (op_name.startswith(('j', 'c')) and op_name[1:] in COND_NAMES):
            cond = COND_ALWAYS
            base_op = op_name
            if op_name.startswith('j') and op_name != 'jmp':
                cond = COND_NAMES[op_name[1:]]
                base_op = 'jmp'
            elif op_name.startswith('c') and op_name != 'call':
                cond = COND_NAMES[op_name[1:]]
                base_op = 'call'
                
            target = op_parts[1].strip() if len(op_parts) > 1 else ""
            mode, ext = parse_operand(target)
            if base_op == 'jmp':
                enc = encode_jmp_abs(cond, mode)
            else:
                enc = encode_call_abs(cond, mode)
            words.append(Word(pc, enc, line.text))
            pc = (pc + 2) & 0xFFFF
            if ext is not None:
                val = eval_expr(ext, symbols, pc) & 0xFFFF
                words.append(Word(pc, val, line.text))
                pc = (pc + 2) & 0xFFFF
            continue

    if not words:
        return b'', words, symbols
    low_addr = min(w.addr for w in words)
    high_addr = max(w.addr for w in words) + 2
    image = bytearray(high_addr - low_addr)
    for w in words:
        off = w.addr - low_addr
        image[off:off+2] = word_to_le(w.value)
    return bytes(image), words, symbols


def write_listing(path: str | Path, words: list[Word]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8') as f:
        for w in words:
            f.write(f"{w.addr:04x}: {w.value:04x}    {w.source}\n")


def write_map(path: str | Path, symbols: dict[str, int]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8') as f:
        for name, value in sorted(symbols.items(), key=lambda kv: (kv[1], kv[0])):
            f.write(f"{value:04x} {name}\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Bootstrap CY16 assembler')
    ap.add_argument('input')
    ap.add_argument('-o', '--output', required=True)
    ap.add_argument('--base', default='0')
    ap.add_argument('--lst')
    ap.add_argument('--map')
    args = ap.parse_args(argv)
    base = eval_expr(args.base) & 0xFFFF
    source = Path(args.input).read_text(encoding='utf-8')
    try:
        image, words, symbols = assemble(source, base=base)
    except Cy16Error as e:
        raise SystemExit(f"cy16-as: error: {e}")
    write_bytes(args.output, image)
    if args.lst:
        write_listing(args.lst, words)
    if args.map:
        write_map(args.map, symbols)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
