from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import re

from .common import Cy16Error, Word, eval_expr, split_operands, strip_comment, u16, word_to_le, write_bytes
from .isa import (
    RET_WORD, MODE_IMM, MODE_DIR_W, MODE_IND_R15, encode_alu, make_reg_mode,
    COND_ALWAYS, encode_jmp_rel, encode_jmp_abs, encode_call_abs, encode_int,
    ALU_OPS, make_ind_reg_mode, COND_NAMES, SPECIAL_OPS, encode_special
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


def _normalize_register_token(token: str) -> str:
    return re.sub(r'%r([0-9]+)', r'r\1', token.lower().strip())


def parse_operand(op: str) -> tuple[int, str | None]:
    """Return (mode, extension-expression-or-None)."""
    low = _normalize_register_token(op)
    if low.startswith('r') and low[1:].isdigit():
        reg = int(low[1:])
        if 0 <= reg <= 15:
            return make_reg_mode(reg), None
    if low in {'[r15++]', '[--r15]', '[r15]'}:
        return MODE_IND_R15, None
    if op.startswith('[') and op.endswith(']'):
        inner = _normalize_register_token(op[1:-1])
        if inner.startswith('r') and inner[1:].isdigit():
            reg = int(inner[1:])
            if 8 <= reg <= 15:
                return make_ind_reg_mode(reg), None
        return MODE_DIR_W, op[1:-1]
    return MODE_IMM, op


def parse_string_literal(token: str) -> bytes:
    try:
        value = ast.literal_eval(token)
    except (SyntaxError, ValueError) as exc:
        raise Cy16Error(f"invalid string literal: {token}") from exc
    if not isinstance(value, str):
        raise Cy16Error(f"expected string literal: {token}")
    return value.encode('latin1')


def directive_bytes(body: str, symbols: dict[str, int], pc: int) -> bytes:
    op, _, rest = body.strip().partition(' ')
    low = op.lower()
    rest = rest.strip()
    if low in {'.ascii', '.asciz'}:
        data = bytearray()
        for item in split_operands(rest):
            data.extend(parse_string_literal(item))
        if low == '.asciz':
            data.append(0)
        return bytes(data)
    if low in {'.space', '.skip'}:
        ops = split_operands(rest)
        if not ops or len(ops) > 2:
            raise Cy16Error(f"{op} requires count and optional fill byte")
        count = eval_expr(ops[0], symbols, pc)
        fill = eval_expr(ops[1], symbols, pc) & 0xFF if len(ops) == 2 else 0
        if count < 0:
            raise Cy16Error(f"{op} count must be non-negative")
        return bytes([fill]) * count
    raise Cy16Error(f"unsupported byte directive: {op}")


def append_bytes_as_words(words: list[Word], pc: int, data: bytes, source: str) -> int:
    start = pc
    padded = data + (b'\x00' if len(data) & 1 else b'')
    for i in range(0, len(padded), 2):
        words.append(Word((start + i) & 0xFFFF, padded[i] | (padded[i + 1] << 8), source))
    return (start + len(data)) & 0xFFFF


def expand_macro(body: str) -> str:
    parts = body.strip().split(None, 1)
    if not parts:
        return body
    op = parts[0].lower()
    operand = parts[1].strip() if len(parts) > 1 else ''
    if op == 'inc':
        if not operand:
            raise Cy16Error('inc requires one operand')
        return f'addi {operand}, 1'
    if op == 'dec':
        if not operand:
            raise Cy16Error('dec requires one operand')
        return f'subi {operand}, 1'
    if op == 'push':
        if not operand:
            raise Cy16Error('push requires one operand')
        return f'mov [r15], {operand}'
    if op == 'pop':
        if not operand:
            raise Cy16Error('pop requires one operand')
        return f'mov {operand}, [r15]'
    return body


def parse_jump_mnemonic(op_name: str) -> tuple[int, str] | None:
    """Return (condition, form), where form is auto, short, or long."""
    low = op_name.lower()
    explicit_form = None
    if low.endswith('.s') or low.endswith('.l'):
        explicit_form = 'short' if low.endswith('.s') else 'long'
        low = low[:-2]

    def base_condition(name: str) -> int | None:
        if name == 'jmp':
            return COND_ALWAYS
        if name.startswith('j') and name[1:] in COND_NAMES:
            return COND_NAMES[name[1:]]
        return None

    cond = base_condition(low)
    if cond is not None:
        return cond, explicit_form or 'auto'

    # Historical suffix form (JZS/JZL, JMPS/JMPL). Exact condition names win
    # above, avoiding ambiguity for mnemonics such as JS and JLS.
    if low.endswith('s') or low.endswith('l'):
        form = 'short' if low.endswith('s') else 'long'
        cond = base_condition(low[:-1])
        if cond is not None:
            return cond, form
    return None


def parse_call_mnemonic(op_name: str) -> int | None:
    low = op_name.lower()
    if low == 'call':
        return COND_ALWAYS
    if low.startswith('c') and low[1:] in COND_NAMES:
        return COND_NAMES[low[1:]]
    return None


def relative_offset_words(pc: int, target: int) -> int:
    next_pc = (pc + 2) & 0xFFFF
    delta = (target - next_pc) & 0xFFFF
    if delta & 0x8000:
        delta -= 0x10000
    if delta & 1:
        raise Cy16Error(f"relative jump target 0x{target:04x} is not word aligned")
    return delta // 2


def jump_target_expression(body: str) -> str:
    parts = body.strip().split(None, 1)
    if len(parts) != 2 or not parts[1].strip():
        raise Cy16Error(f"{parts[0] if parts else 'jump'} requires a target")
    return parts[1].strip()


def estimate_words(body: str, auto_jump_words: int = 2) -> int:
    if not body:
        return 0
    body = expand_macro(body)
    low = body.strip().lower()
    if low.startswith(('.org', '.equ', '.global', '.globl', '.section', '.include', '.text', '.data', '.bss')):
        return 0
    if low.startswith(('.short', '.word')):
        return len(split_operands(body.split(None, 1)[1] if len(body.split(None, 1)) > 1 else ''))
    if low.startswith('.byte'):
        n = len(split_operands(body.split(None, 1)[1] if len(body.split(None, 1)) > 1 else ''))
        return (n + 1) // 2
    if low.startswith(('.ascii', '.asciz')):
        data = bytearray()
        for item in split_operands(body.split(None, 1)[1] if len(body.split(None, 1)) > 1 else ''):
            data.extend(parse_string_literal(item))
        if low.startswith('.asciz'):
            data.append(0)
        return (len(data) + 1) // 2
    if low.startswith(('.space', '.skip')):
        return 0
    if low == 'ret' or low.startswith('int '):
        return 1

    op_parts = low.split(None, 1)
    op_name = op_parts[0]
    if op_name in ALU_OPS:
        ops = split_operands(op_parts[1].strip() if len(op_parts) > 1 else '')
        if len(ops) == 2:
            src_mode, src_ext = parse_operand(ops[1])
            dst_mode, dst_ext = parse_operand(ops[0])
            return 1 + (1 if src_ext is not None else 0) + (1 if dst_ext is not None else 0)

    if op_name in SPECIAL_OPS:
        ops = split_operands(op_parts[1].strip() if len(op_parts) > 1 else '')
        if len(ops) == 2:
            _, ext = parse_operand(ops[0])
            return 1 + (1 if ext is not None else 0)

    jump = parse_jump_mnemonic(op_name)
    if jump is not None:
        _, form = jump
        return 1 if form == 'short' else (2 if form == 'long' else auto_jump_words)

    if parse_call_mnemonic(op_name) is not None:
        target = op_parts[1].strip() if len(op_parts) > 1 else ''
        _, ext = parse_operand(target)
        return 1 + (1 if ext is not None else 0)

    raise Cy16Error(f"cannot estimate size for unsupported statement: {body}")


def first_pass(lines: list[Line], base: int, auto_sizes: dict[int, int]) -> dict[str, int]:
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
            continue
        if low.startswith(('.global', '.globl', '.section', '.include', '.text', '.data', '.bss')):
            continue
        if low.startswith(('.ascii', '.asciz', '.space', '.skip')):
            pc = (pc + len(directive_bytes(body, symbols, pc))) & 0xFFFF
            continue
        pc = (pc + estimate_words(body, auto_sizes.get(line.number, 2)) * 2) & 0xFFFF
    return symbols


def resolve_layout(lines: list[Line], base: int) -> tuple[dict[str, int], dict[int, int]]:
    auto_sizes: dict[int, int] = {}
    for line in lines:
        body = expand_macro(line.body.strip()) if line.body.strip() else ''
        op_name = body.split(None, 1)[0].lower() if body else ''
        jump = parse_jump_mnemonic(op_name)
        if jump is not None and jump[1] == 'auto':
            auto_sizes[line.number] = 2

    for _ in range(max(4, len(lines) + 1)):
        symbols = first_pass(lines, base, auto_sizes)
        changed = False
        for line in lines:
            if line.number not in auto_sizes or line.addr is None:
                continue
            body = expand_macro(line.body.strip())
            target_expr = jump_target_expression(body)
            try:
                target = eval_expr(target_expr, symbols, line.addr) & 0xFFFF
                offset = relative_offset_words(line.addr, target)
                desired = 1 if -64 <= offset <= 63 else 2
            except (Cy16Error, ValueError, KeyError, NameError, SyntaxError):
                desired = 2
            if auto_sizes[line.number] != desired:
                auto_sizes[line.number] = desired
                changed = True
        if not changed:
            return symbols, auto_sizes
    raise Cy16Error('jump relaxation did not converge')


def assemble(source: str, base: int = 0) -> tuple[bytes, list[Word], dict[str, int]]:
    lines = parse_source(source)
    symbols, auto_sizes = resolve_layout(lines, base)
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
        if low.startswith(('.equ', '.global', '.globl', '.section', '.include', '.text', '.data', '.bss')):
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
            pc = append_bytes_as_words(words, pc, bytes(vals), line.text)
            continue
        if low.startswith(('.ascii', '.asciz', '.space', '.skip')):
            pc = append_bytes_as_words(words, pc, directive_bytes(body, symbols, pc), line.text)
            continue

        body = expand_macro(body)
        low = body.lower()
        if low == 'ret':
            words.append(Word(pc, RET_WORD, line.text))
            pc = (pc + 2) & 0xFFFF
            continue

        op_parts = body.split(None, 1)
        op_name = op_parts[0].lower()

        if op_name == 'int':
            if len(op_parts) != 2:
                raise Cy16Error(f"line {line.number}: int requires a vector")
            vector = eval_expr(op_parts[1], symbols, pc)
            try:
                enc = encode_int(vector)
            except ValueError as exc:
                raise Cy16Error(f"line {line.number}: {exc}") from exc
            words.append(Word(pc, enc, line.text))
            pc = (pc + 2) & 0xFFFF
            continue

        if op_name in ALU_OPS:
            ops = split_operands(op_parts[1].strip() if len(op_parts) > 1 else '')
            if len(ops) != 2:
                raise Cy16Error(f"line {line.number}: {op_name} requires two operands")
            dst, src = ops
            src_mode, src_ext = parse_operand(src)
            dst_mode, dst_ext = parse_operand(dst)
            enc = encode_alu(ALU_OPS[op_name], src_mode, dst_mode)
            words.append(Word(pc, enc, line.text))
            pc = (pc + 2) & 0xFFFF
            if src_ext is not None:
                words.append(Word(pc, eval_expr(src_ext, symbols, pc) & 0xFFFF, line.text))
                pc = (pc + 2) & 0xFFFF
            if dst_ext is not None:
                words.append(Word(pc, eval_expr(dst_ext, symbols, pc) & 0xFFFF, line.text))
                pc = (pc + 2) & 0xFFFF
            continue

        if op_name in SPECIAL_OPS:
            ops = split_operands(op_parts[1].strip() if len(op_parts) > 1 else '')
            if len(ops) != 2:
                raise Cy16Error(f"line {line.number}: {op_name} requires two operands")
            dst, count_expr = ops
            dst_mode, dst_ext = parse_operand(dst)
            count = eval_expr(count_expr, symbols, pc)
            if not 1 <= count <= 8:
                raise Cy16Error(f"line {line.number}: shift/addi count must be 1-8")
            enc = encode_special(SPECIAL_OPS[op_name], count, dst_mode)
            words.append(Word(pc, enc, line.text))
            pc = (pc + 2) & 0xFFFF
            if dst_ext is not None:
                words.append(Word(pc, eval_expr(dst_ext, symbols, pc) & 0xFFFF, line.text))
                pc = (pc + 2) & 0xFFFF
            continue

        jump = parse_jump_mnemonic(op_name)
        if jump is not None:
            cond, form = jump
            target_expr = jump_target_expression(body)
            use_short = form == 'short' or (form == 'auto' and auto_sizes.get(line.number) == 1)
            if use_short:
                target = eval_expr(target_expr, symbols, pc) & 0xFFFF
                offset = relative_offset_words(pc, target)
                if not -64 <= offset <= 63:
                    raise Cy16Error(
                        f"line {line.number}: forced-short jump offset {offset} outside -64..63"
                    )
                words.append(Word(pc, encode_jmp_rel(cond, offset), line.text))
                pc = (pc + 2) & 0xFFFF
            else:
                mode, ext = parse_operand(target_expr)
                words.append(Word(pc, encode_jmp_abs(cond, mode), line.text))
                pc = (pc + 2) & 0xFFFF
                if ext is not None:
                    words.append(Word(pc, eval_expr(ext, symbols, pc) & 0xFFFF, line.text))
                    pc = (pc + 2) & 0xFFFF
            continue

        call_cond = parse_call_mnemonic(op_name)
        if call_cond is not None:
            if len(op_parts) != 2:
                raise Cy16Error(f"line {line.number}: {op_name} requires a target")
            mode, ext = parse_operand(op_parts[1].strip())
            words.append(Word(pc, encode_call_abs(call_cond, mode), line.text))
            pc = (pc + 2) & 0xFFFF
            if ext is not None:
                words.append(Word(pc, eval_expr(ext, symbols, pc) & 0xFFFF, line.text))
                pc = (pc + 2) & 0xFFFF
            continue

        raise Cy16Error(f"line {line.number}: unsupported statement: {line.body}")

    if not words:
        return b'', words, symbols
    low_addr = min(w.addr for w in words)
    high_addr = max(w.addr for w in words) + 2
    image = bytearray(high_addr - low_addr)
    for word in words:
        off = word.addr - low_addr
        image[off:off + 2] = word_to_le(word.value)
    return bytes(image), words, symbols


def write_listing(path: str | Path, words: list[Word]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8') as f:
        for word in words:
            f.write(f"{word.addr:04x}: {word.value:04x}    {word.source}\n")


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
    except Cy16Error as exc:
        raise SystemExit(f"cy16-as: error: {exc}")
    write_bytes(args.output, image)
    if args.lst:
        write_listing(args.lst, words)
    if args.map:
        write_map(args.map, symbols)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
