from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto

class Op(Enum):
    IMM = auto()
    LOAD = auto()
    STORE = auto()
    ADD = auto()
    SUB = auto()
    CMP = auto()
    AND = auto()
    OR = auto()
    XOR = auto()
    MOV = auto()
    LABEL = auto()
    JMP = auto()
    CALL = auto()
    RET = auto()
    PUSH = auto()
    POP = auto()

@dataclass
class IRInst:
    op: Op
    args: list[any]
    comment: str = ""

@dataclass
class IRFunc:
    name: str
    insts: list[IRInst]

@dataclass
class IRProgram:
    funcs: list[IRFunc]
    globals: list[tuple[str, int]] # name, init_val
