from __future__ import annotations

# Opcode constants (top 4 bits)
OP_MOV  = 0x0
OP_ADD  = 0x1
OP_ADDC = 0x2
OP_SUB  = 0x3
OP_SUBB = 0x4
OP_CMP  = 0x5
OP_AND  = 0x6
OP_TEST = 0x7
OP_OR   = 0x8
OP_XOR  = 0x9

ALU_OPS = {
    'mov': OP_MOV,
    'add': OP_ADD,
    'addc': OP_ADDC,
    'sub': OP_SUB,
    'subb': OP_SUBB,
    'cmp': OP_CMP,
    'and': OP_AND,
    'test': OP_TEST,
    'or': OP_OR,
    'xor': OP_XOR,
}

ALU_NAMES = {v: k for k, v in ALU_OPS.items()}

# Special opcodes prefix 1101 (0xD)
OP_SPECIAL_PREFIX = 0xD
SPECIAL_OPS = {
    'shr': 0b000,
    'shl': 0b001,
    'ror': 0b010,
    'rol': 0b011,
    'addi': 0b100,
    'subi': 0b101,
}
SPECIAL_NAMES = {v: k for k, v in SPECIAL_OPS.items()}

# Special opcodes
OP_JMP_RET_PREFIX = 0xC  # 1100
OP_CALL_PREFIX    = 0xA  # 1010

# Conditions
COND_Z      = 0x0  # EQ
COND_NZ     = 0x1  # NE
COND_C      = 0x2  # LO
COND_NC     = 0x3  # HS
COND_S      = 0x4
COND_NS     = 0x5
COND_O      = 0x6
COND_NO     = 0x7
COND_A      = 0x8  # HI
COND_BE     = 0x9  # LS
COND_G      = 0xA
COND_GE     = 0xB
COND_L      = 0xC
COND_LE     = 0xD
COND_ALWAYS = 0xF

COND_NAMES = {
    'z': COND_Z, 'eq': COND_Z,
    'nz': COND_NZ, 'ne': COND_NZ,
    'c': COND_C, 'lo': COND_C,
    'nc': COND_NC, 'hs': COND_NC,
    's': COND_S, 'ns': COND_NS,
    'o': COND_O, 'no': COND_NO,
    'a': COND_A, 'hi': COND_A,
    'be': COND_BE, 'ls': COND_BE,
    'g': COND_G, 'ge': COND_GE,
    'l': COND_L, 'le': COND_LE,
    'always': COND_ALWAYS,
}

# Inverse condition map for disassembly
COND_CODE_NAMES = {
    0x0: 'z', 0x1: 'nz', 0x2: 'c', 0x3: 'nc',
    0x4: 's', 0x5: 'ns', 0x6: 'o', 0x7: 'no',
    0x8: 'a', 0x9: 'be', 0xA: 'g', 0xB: 'ge',
    0xC: 'l', 0xD: 'le', 0xF: 'always',
}

# RET word: 1100 1111 1001 0111 (JMP always [R15])
RET_WORD = 0xCF97

# Operand modes (6 bits)
MODE_REG_MASK = 0b110000
MODE_REG_VAL = 0b000000
MODE_IMM = 0b011111
MODE_DIR_W = 0b100111
MODE_IND_R_MASK = 0b111000
MODE_IND_R_VAL = 0b010000
MODE_IND_R15 = 0b010111

def encode_alu(op: int, src_mode: int, dst_mode: int) -> int:
    return (op << 12) | ((src_mode & 0x3F) << 6) | (dst_mode & 0x3F)

def encode_special(op: int, count: int, dst_mode: int) -> int:
    # count is 1-8, stored as 0-7
    return (OP_SPECIAL_PREFIX << 12) | ((op & 0x7) << 9) | (((count - 1) & 0x7) << 6) | (dst_mode & 0x3F)

def encode_jmp_abs(cond: int, dst_mode: int) -> int:
    return (OP_JMP_RET_PREFIX << 12) | (cond << 8) | (1 << 7) | (dst_mode & 0x3F)

def encode_call_abs(cond: int, dst_mode: int) -> int:
    return (OP_CALL_PREFIX << 12) | (cond << 8) | (1 << 7) | (dst_mode & 0x3F)

def is_reg_mode(mode: int) -> bool:
    return (mode & MODE_REG_MASK) == MODE_REG_VAL

def get_reg_from_mode(mode: int) -> int:
    return mode & 0b001111

def make_reg_mode(reg: int) -> int:
    return MODE_REG_VAL | (reg & 0b001111)

def is_ind_reg_mode(mode: int) -> bool:
    return (mode & MODE_IND_R_MASK) == MODE_IND_R_VAL

def get_ind_reg_from_mode(mode: int) -> int:
    return (mode & 0b000111) + 8

def make_ind_reg_mode(reg: int) -> int:
    return MODE_IND_R_VAL | ((reg - 8) & 0b000111)

