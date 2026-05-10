from __future__ import annotations
import sys
from pycparser import c_parser, c_ast
from .ir import IRProgram, IRFunc, IRInst, Op

class CY16Backend:
    def __init__(self):
        self.label_count = 0
        self.locals = {}

    def gen_label(self) -> str:
        self.label_count += 1
        return f"L{self.label_count}"

    def compile(self, node: c_ast.Node) -> list[str]:
        lines = []
        if isinstance(node, c_ast.FileAST):
            for ext in node.ext:
                lines.extend(self.compile(ext))
        elif isinstance(node, c_ast.FuncDef):
            name = node.decl.name
            self.locals = {}
            if node.decl.type.args:
                for i, param in enumerate(node.decl.type.args.params):
                    if hasattr(param, 'name') and param.name:
                        self.locals[param.name] = f"r{i}"
            
            lines.append(f".global _{name}")
            lines.append(f"_{name}:")
            lines.extend(self.compile(node.body))
            lines.append(f".L_ret_{name}:")
            lines.append("    ret")
            lines.append("")
        elif isinstance(node, c_ast.Compound):
            for stmt in node.block_items or []:
                lines.extend(self.compile(stmt))
        elif isinstance(node, c_ast.Return):
            if node.expr:
                lines.extend(self.gen_expr(node.expr, "r0"))
            lines.append("    ret")
        elif isinstance(node, c_ast.Assignment):
            if node.op == '=':
                lines.extend(self.gen_expr(node.rvalue, "r0"))
                if isinstance(node.lvalue, c_ast.ID):
                    if node.lvalue.name in self.locals:
                        lines.append(f"    mov {self.locals[node.lvalue.name]}, r0")
                    else:
                        lines.append(f"    mov [_{node.lvalue.name}], r0")
                elif isinstance(node.lvalue, c_ast.UnaryOp) and node.lvalue.op == '*':
                    lines.append("    mov [--r15], r0")
                    lines.extend(self.gen_expr(node.lvalue.expr, "r8"))
                    lines.append("    mov r0, [r15++]")
                    lines.append("    mov [r8], r0")
        elif isinstance(node, c_ast.If):
            l_else = self.gen_label()
            l_end = self.gen_label()
            lines.extend(self.gen_expr(node.cond, "r0"))
            lines.append("    cmp r0, 0")
            lines.append(f"    jz {l_else}")
            lines.extend(self.compile(node.iftrue))
            lines.append(f"    jmp {l_end}")
            lines.append(f"{l_else}:")
            if node.iffalse:
                lines.extend(self.compile(node.iffalse))
            lines.append(f"{l_end}:")
        elif isinstance(node, c_ast.While):
            l_start = self.gen_label()
            l_end = self.gen_label()
            lines.append(f"{l_start}:")
            lines.extend(self.gen_expr(node.cond, "r0"))
            lines.append("    cmp r0, 0")
            lines.append(f"    jz {l_end}")
            lines.extend(self.compile(node.stmt))
            lines.append(f"    jmp {l_start}")
            lines.append(f"{l_end}:")
        elif isinstance(node, c_ast.FuncCall):
            # This is a statement call (return value ignored)
            lines.extend(self.gen_expr(node, "r0"))
        return lines

    def gen_expr(self, node: c_ast.Node, dst: str) -> list[str]:
        lines = []
        if isinstance(node, c_ast.Constant):
            lines.append(f"    mov {dst}, {node.value}")
        elif isinstance(node, c_ast.ID):
            if node.name in self.locals:
                lines.append(f"    mov {dst}, {self.locals[node.name]}")
            else:
                lines.append(f"    mov {dst}, [_{node.name}]")
        elif isinstance(node, c_ast.BinaryOp):
            lines.extend(self.gen_expr(node.left, "r0"))
            lines.append("    mov [--r15], r0")
            lines.extend(self.gen_expr(node.right, "r1"))
            lines.append("    mov r0, [r15++]")
            if node.op == '+':
                lines.append(f"    mov {dst}, r0")
                lines.append(f"    add {dst}, r1")
            elif node.op == '-':
                lines.append(f"    mov {dst}, r0")
                lines.append(f"    sub {dst}, r1")
            elif node.op == '<':
                lines.append("    cmp r0, r1")
                l_true = self.gen_label()
                l_done = self.gen_label()
                lines.append(f"    jc {l_true}") # Carry set if r0 < r1
                lines.append(f"    mov {dst}, 0")
                lines.append(f"    jmp {l_done}")
                lines.append(f"{l_true}:")
                lines.append(f"    mov {dst}, 1")
                lines.append(f"{l_done}:")
        elif isinstance(node, c_ast.UnaryOp) and node.op == '*':
            lines.extend(self.gen_expr(node.expr, "r8"))
            lines.append(f"    mov {dst}, [r8]")
        elif isinstance(node, c_ast.FuncCall):
            if node.args:
                for i, arg in enumerate(node.args.exprs):
                    lines.extend(self.gen_expr(arg, f"r{i}"))
            lines.append(f"    call _{node.name.name}")
            lines.append(f"    mov {dst}, r0")
        elif isinstance(node, c_ast.Cast):
            lines.extend(self.gen_expr(node.expr, dst))
        return lines

def compile_c(source: str) -> str:
    parser = c_parser.CParser()
    try:
        ast = parser.parse(source)
    except Exception as e:
        return f"; Error parsing: {e}"
    
    backend = CY16Backend()
    lines = backend.compile(ast)
    return "\n".join(lines)
