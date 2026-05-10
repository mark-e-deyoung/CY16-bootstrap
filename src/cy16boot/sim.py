from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field

from .common import le_to_word, read_bytes, word_to_le
from .isa import (
    RET_WORD, MODE_IMM, MODE_DIR_W, MODE_IND_R15, is_reg_mode, get_reg_from_mode,
    ALU_NAMES, OP_JMP_RET_PREFIX, OP_CALL_PREFIX, COND_ALWAYS,
    is_ind_reg_mode, get_ind_reg_from_mode,
    OP_SPECIAL_PREFIX, SPECIAL_NAMES,
    COND_Z, COND_NZ, COND_C, COND_NC, COND_S, COND_NS, COND_O, COND_NO,
    COND_A, COND_BE, COND_G, COND_GE, COND_L, COND_LE
)

@dataclass
class CPU:
    memory: bytearray = field(default_factory=lambda: bytearray(65536))
    regs: list[int] = field(default_factory=lambda: [0] * 16)
    pc: int = 0
    halted: bool = False
    steps: int = 0
    
    # Flags
    fz: bool = False
    fc: bool = False
    fs: bool = False
    fo: bool = False

    def load(self, data: bytes, base: int) -> None:
        self.memory[base:base+len(data)] = data

    def readw(self, addr: int) -> int:
        return self.memory[addr & 0xFFFF] | (self.memory[(addr + 1) & 0xFFFF] << 8)

    def writew(self, addr: int, value: int) -> None:
        b = word_to_le(value)
        self.memory[addr & 0xFFFF] = b[0]
        self.memory[(addr + 1) & 0xFFFF] = b[1]

    def get_op_val(self, mode: int) -> tuple[int, str]:
        if is_reg_mode(mode):
            reg = get_reg_from_mode(mode)
            return self.regs[reg], f"r{reg}"
        if mode == MODE_IMM:
            val = self.readw(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            return val, f"0x{val:04x}"
        if mode == MODE_DIR_W:
            addr = self.readw(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            val = self.readw(addr)
            return val, f"[0x{addr:04x}]"
        if mode == MODE_IND_R15:
            val = self.readw(self.regs[15])
            self.regs[15] = (self.regs[15] + 2) & 0xFFFF
            return val, "[r15++]"
        if is_ind_reg_mode(mode):
            reg = get_ind_reg_from_mode(mode)
            val = self.readw(self.regs[reg])
            return val, f"[r{reg}]"
        raise RuntimeError(f"unsupported src mode: {mode}")

    def set_op_val(self, mode: int, val: int) -> str:
        if is_reg_mode(mode):
            reg = get_reg_from_mode(mode)
            self.regs[reg] = val
            return f"r{reg}"
        if mode == MODE_DIR_W:
            addr = self.readw(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.writew(addr, val)
            return f"[0x{addr:04x}]"
        if mode == MODE_IND_R15:
            self.regs[15] = (self.regs[15] - 2) & 0xFFFF
            self.writew(self.regs[15], val)
            return "[--r15]"
        if is_ind_reg_mode(mode):
            reg = get_ind_reg_from_mode(mode)
            self.writew(self.regs[reg], val)
            return f"[r{reg}]"
        raise RuntimeError(f"unsupported dst mode: {mode}")

    def check_cond(self, cond: int) -> bool:
        if cond == COND_ALWAYS: return True
        if cond == COND_Z:  return self.fz
        if cond == COND_NZ: return not self.fz
        if cond == COND_C:  return self.fc
        if cond == COND_NC: return not self.fc
        if cond == COND_S:  return self.fs
        if cond == COND_NS: return not self.fs
        if cond == COND_O:  return self.fo
        if cond == COND_NO: return not self.fo
        if cond == COND_A:  return not self.fc and not self.fz
        if cond == COND_BE: return self.fc or self.fz
        if cond == COND_G:  return (self.fs == self.fo) and not self.fz
        if cond == COND_GE: return (self.fs == self.fo)
        if cond == COND_L:  return (self.fs != self.fo)
        if cond == COND_LE: return (self.fs != self.fo) or self.fz
        return False

    def update_flags(self, res: int, op1: int, op2: int, op_type: str):
        self.fz = (res == 0)
        self.fs = (res & 0x8000) != 0
        if op_type == 'add' or op_type == 'addi':
            self.fc = (op1 + op2) > 0xFFFF
            self.fo = ((op1 ^ res) & (op2 ^ res) & 0x8000) != 0
        elif op_type == 'sub' or op_type == 'subi' or op_type == 'cmp':
            self.fc = op1 < op2
            self.fo = ((op1 ^ op2) & (op1 ^ res) & 0x8000) != 0
        elif op_type in ('and', 'or', 'xor', 'test', 'shl', 'shr', 'rol', 'ror'):
            self.fc = False # Simplified for now
            self.fo = False

    def step(self) -> str:
        pc0 = self.pc
        w = self.readw(self.pc)
        if w == RET_WORD:
            self.pc = self.readw(self.regs[15])
            self.regs[15] = (self.regs[15] + 2) & 0xFFFF
            self.steps += 1
            if self.pc == 0: self.halted = True
            return f"{self.steps:06d} pc=0x{pc0:04x} ret ; new pc=0x{self.pc:04x}"

        opcode = (w >> 12)
        if opcode in ALU_NAMES:
            op_name = ALU_NAMES[opcode]
            src_mode = (w >> 6) & 0x3F
            dst_mode = w & 0x3F
            self.pc = (self.pc + 2) & 0xFFFF
            
            src_val, src_str = self.get_op_val(src_mode)
            dst_val = 0
            if op_name != 'mov':
                if is_reg_mode(dst_mode):
                    dst_val = self.regs[get_reg_from_mode(dst_mode)]
                elif is_ind_reg_mode(dst_mode):
                    dst_val = self.readw(self.regs[get_ind_reg_from_mode(dst_mode)])
                elif dst_mode == MODE_DIR_W:
                    addr = self.readw(self.pc)
                    dst_val = self.readw(addr)

            if op_name == 'mov': res = src_val
            elif op_name == 'add': res = (dst_val + src_val) & 0xFFFF
            elif op_name == 'sub' or op_name == 'cmp': res = (dst_val - src_val) & 0xFFFF
            elif op_name == 'and' or op_name == 'test': res = dst_val & src_val
            elif op_name == 'or': res = dst_val | src_val
            elif op_name == 'xor': res = dst_val ^ src_val
            else: res = src_val

            self.update_flags(res, dst_val, src_val, op_name)
            
            if op_name != 'cmp' and op_name != 'test':
                dst_str = self.set_op_val(dst_mode, res)
            else:
                if dst_mode == MODE_DIR_W:
                    self.pc = (self.pc + 2) & 0xFFFF
                    dst_str = f"[0x{self.readw(self.pc-2):04x}]"
                elif is_reg_mode(dst_mode):
                    dst_str = f"r{get_reg_from_mode(dst_mode)}"
                elif is_ind_reg_mode(dst_mode):
                    dst_str = f"[r{get_ind_reg_from_mode(dst_mode)}]"
                else: dst_str = "?"

            text = f"{op_name} {dst_str}, {src_str} ; res=0x{res:04x}"
            self.steps += 1
            return f"{self.steps:06d} pc=0x{pc0:04x} {text}"

        if opcode == OP_SPECIAL_PREFIX:
            special_op = (w >> 9) & 0x7
            count = ((w >> 6) & 0x7) + 1
            dst_mode = w & 0x3F
            self.pc = (self.pc + 2) & 0xFFFF
            
            op_name = SPECIAL_NAMES[special_op]
            dst_val = 0
            if is_reg_mode(dst_mode):
                dst_val = self.regs[get_reg_from_mode(dst_mode)]
            elif is_ind_reg_mode(dst_mode):
                dst_val = self.readw(self.regs[get_ind_reg_from_mode(dst_mode)])
            elif dst_mode == MODE_DIR_W:
                addr = self.readw(self.pc)
                dst_val = self.readw(addr)
            
            if op_name == 'shl': res = (dst_val << count) & 0xFFFF
            elif op_name == 'shr': res = (dst_val >> count) & 0xFFFF
            elif op_name == 'addi': res = (dst_val + count) & 0xFFFF
            elif op_name == 'subi': res = (dst_val - count) & 0xFFFF
            else: res = dst_val
            
            self.update_flags(res, dst_val, count, op_name)
            dst_str = self.set_op_val(dst_mode, res)
            text = f"{op_name} {dst_str}, {count} ; res=0x{res:04x}"
            self.steps += 1
            return f"{self.steps:06d} pc=0x{pc0:04x} {text}"

        if opcode == OP_JMP_RET_PREFIX or opcode == OP_CALL_PREFIX:
            op_name = 'jmp' if opcode == OP_JMP_RET_PREFIX else 'call'
            cond = (w >> 8) & 0xF
            is_abs = (w >> 7) & 1
            dst_mode = w & 0x3F
            self.pc = (self.pc + 2) & 0xFFFF
            
            if is_abs:
                target, target_str = self.get_op_val(dst_mode)
                if self.check_cond(cond):
                    if op_name == 'call':
                        self.regs[15] = (self.regs[15] - 2) & 0xFFFF
                        self.writew(self.regs[15], self.pc)
                    self.pc = target
                    taken = True
                else:
                    taken = False
                self.steps += 1
                return f"{self.steps:06d} pc=0x{pc0:04x} {op_name} {target_str} {'TAKEN' if taken else 'not taken'} ; new pc=0x{self.pc:04x}"

        raise RuntimeError(f"unsupported instruction at 0x{pc0:04x}: 0x{w:04x}")


def run(data: bytes, base: int, pc: int, max_steps: int, initial_regs: list[int] | None = None) -> tuple[CPU, list[str]]:
    cpu = CPU(pc=pc)
    if initial_regs:
        cpu.regs = list(initial_regs)
    cpu.load(data, base)
    trace: list[str] = []
    while not cpu.halted and cpu.steps < max_steps:
        try:
            trace.append(cpu.step())
        except Exception as e:
            trace.append(f"ERROR: {e}")
            break
    return cpu, trace


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Bootstrap CY16 simulator')
    ap.add_argument('input')
    ap.add_argument('--base', default='0')
    ap.add_argument('--pc', default=None)
    ap.add_argument('--max-steps', type=int, default=100)
    ap.add_argument('--dump', action='append', default=[], help='dump word at address after run')
    ap.add_argument('--reg', action='append', default=[], help='set register: rN=VAL')
    ap.add_argument('--dump-regs', action='store_true', help='dump all registers after run')
    args = ap.parse_args(argv)
    
    initial_regs = [0] * 16
    for reg_spec in args.reg:
        if '=' not in reg_spec: continue
        name, val_str = reg_spec.split('=', 1)
        idx = int(name[1:])
        initial_regs[idx] = int(val_str, 0) & 0xFFFF

    base = int(args.base, 0)
    pc = int(args.pc, 0) if args.pc is not None else base
    cpu, trace = run(read_bytes(args.input), base, pc, args.max_steps, initial_regs=initial_regs)
    
    for line in trace: print(line)
    if args.dump_regs:
        for i in range(0, 16, 4):
            print(" ".join(f"r{j:02d}=0x{cpu.regs[j]:04x}" for j in range(i, i+4)))
    for addr_text in args.dump:
        addr = int(addr_text, 0)
        print(f"mem[0x{addr:04x}]=0x{cpu.readw(addr):04x}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
