"""Opt-in architectural register-window model for CY16 RDTE.

This is a standalone model, not yet wired into the instruction simulator.
It intentionally excludes unspecified peripheral and illegal-access behavior.
Source: CY16 Programmer's Guide v1.1, §§1.3.3–1.3.4.
"""
from dataclasses import dataclass, field


@dataclass
class RegisterWindow:
    memory: bytearray = field(default_factory=lambda: bytearray(65536))
    regbank: int = 0x0100

    @staticmethod
    def address(bank: int, register: int) -> int:
        if not 0 <= register < 16:
            raise ValueError("CY16 register must be R0 through R15")
        return ((bank & 0xFFE0) | (register << 1)) & 0xFFFF

    def read_register(self, register: int) -> int:
        addr = self.address(self.regbank, register)
        return self.memory[addr] | (self.memory[addr + 1] << 8)

    def write_register(self, register: int, value: int) -> None:
        addr = self.address(self.regbank, register)
        self.memory[addr] = value & 0xFF
        self.memory[addr + 1] = (value >> 8) & 0xFF

    def select_bank(self, value: int) -> None:
        self.regbank = value & 0xFFFF
