from __future__ import annotations

from typing import Any

from . import sim_core as core

MEMORY_SIZE = 0x10000


class CPU(core.CPU):
    """CY16 CPU model with a fail-closed 64 KiB image-loading boundary."""

    def load(self, data: bytes, base: int) -> None:
        if not isinstance(data, bytes):
            raise TypeError("simulator image must be bytes")
        if isinstance(base, bool) or not isinstance(base, int):
            raise TypeError("simulator base must be an integer")
        if not 0 <= base < MEMORY_SIZE:
            raise ValueError("simulator base must be in 0..0xffff")
        end = base + len(data)
        if end > MEMORY_SIZE:
            raise ValueError("simulator image exceeds the 64 KiB CY16 address space")
        if len(self.memory) != MEMORY_SIZE:
            raise RuntimeError("simulator memory model is not exactly 64 KiB")
        self.memory[base:end] = data
        if len(self.memory) != MEMORY_SIZE:
            raise RuntimeError("simulator load changed the 64 KiB memory size")


def run(
    data: bytes,
    base: int,
    pc: int,
    max_steps: int,
    initial_regs: list[int] | None = None,
) -> tuple[CPU, list[str]]:
    cpu = CPU(pc=pc)
    if initial_regs:
        cpu.regs = list(initial_regs)
    cpu.load(data, base)
    trace: list[str] = []
    while not cpu.halted and cpu.steps < max_steps:
        try:
            trace.append(cpu.step())
        except Exception as exc:
            trace.append(f"ERROR: {exc}")
            break
    return cpu, trace


# Keep the established command-line implementation, but make its module globals
# use the bounded CPU/run entry points above.
core.CPU = CPU
core.run = run
main = core.main


def __getattr__(name: str) -> Any:
    """Preserve access to established simulator constants and helpers."""

    return getattr(core, name)


if __name__ == "__main__":
    raise SystemExit(main())
