from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import ast
import operator as op

OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.LShift: op.lshift,
    ast.RShift: op.rshift,
    ast.BitOr: op.or_,
    ast.BitAnd: op.and_,
    ast.BitXor: op.xor,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
    ast.Invert: op.invert,
}

class Cy16Error(Exception):
    pass

@dataclass(frozen=True)
class Word:
    addr: int
    value: int
    source: str = ""


def u16(value: int) -> int:
    return value & 0xFFFF


def word_to_le(value: int) -> bytes:
    value &= 0xFFFF
    return bytes((value & 0xFF, (value >> 8) & 0xFF))


def le_to_word(data: bytes, offset: int = 0) -> int:
    return data[offset] | (data[offset + 1] << 8)


def ensure_even_address(addr: int) -> None:
    if addr & 1:
        raise Cy16Error(f"word address must be even: 0x{addr:04x}")


def read_bytes(path: str | Path) -> bytes:
    return Path(path).read_bytes()


def write_bytes(path: str | Path, data: bytes) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def eval_expr(expr: str, symbols: dict[str, int] | None = None, current_addr: int = 0) -> int:
    """Evaluate a small assembler expression safely."""
    symbols = dict(symbols or {})
    symbols.setdefault('.', current_addr)
    expr = expr.strip()
    if not expr:
        raise Cy16Error("empty expression")
    # Accept common assembler hex suffix such as 1234h.
    tokens = []
    for tok in expr.replace('(', ' ( ').replace(')', ' ) ').replace(',', ' , ').split():
        if tok.lower().endswith('h') and tok[:-1]:
            try:
                int(tok[:-1], 16)
                tok = '0x' + tok[:-1]
            except ValueError:
                pass
        tokens.append(tok)
    expr = ' '.join(tokens)
    node = ast.parse(expr, mode='eval').body
    return _eval_node(node, symbols) & 0xFFFFFFFF


def _eval_node(node: ast.AST, symbols: dict[str, int]) -> int:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return int(node.value)
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) == 1:
        return ord(node.value)
    if isinstance(node, ast.Name):
        if node.id in symbols:
            return symbols[node.id]
        raise Cy16Error(f"unknown symbol in expression: {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval_node(node.left, symbols), _eval_node(node.right, symbols))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval_node(node.operand, symbols))
    raise Cy16Error(f"unsupported expression syntax: {ast.dump(node)}")


def strip_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    out = []
    for ch in line:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if quote and ch == '\\':
            out.append(ch)
            escaped = True
            continue
        if ch in {'"', "'"}:
            if quote == ch:
                quote = None
            elif quote is None:
                quote = ch
        if quote is None and ch in {';', '#'}:
            break
        out.append(ch)
    return ''.join(out).strip()


def split_operands(text: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    quote: str | None = None
    escaped = False
    cur = []
    for ch in text:
        if escaped:
            cur.append(ch)
            escaped = False
            continue
        if quote and ch == '\\':
            cur.append(ch)
            escaped = True
            continue
        if ch in {'"', "'"}:
            if quote == ch:
                quote = None
            elif quote is None:
                quote = ch
        if quote is None and ch in '([':
            depth += 1
        elif quote is None and ch in ')]':
            depth -= 1
        if quote is None and ch == ',' and depth == 0:
            parts.append(''.join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur or text.endswith(','):
        parts.append(''.join(cur).strip())
    return parts
