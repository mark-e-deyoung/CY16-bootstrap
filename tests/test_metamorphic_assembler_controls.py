"""Bounded metamorphic controls for the existing CY16 assembler.

Independent of historical vendor executables and physical hardware.
The transformed source is equivalent by construction: comments and blank lines
must not alter machine-code bytes. This tests assembly stability, not C or ISA correctness.
"""
from pathlib import Path
import subprocess
import sys


def _assemble(source: str, output: Path, work: Path) -> bytes:
    asm = work / (output.stem + ".s")
    asm.write_text(source, encoding="utf-8")
    subprocess.run(
        [sys.executable, "-m", "cy16boot.asm", str(asm),
         "-o", str(output), "--base", "0x1000"],
        check=True, capture_output=True, text=True,
    )
    return output.read_bytes()


def test_comment_whitespace_metamorphism(tmp_path):
    baseline = """
.org 0x1000
_start:
    mov [0xc03a], 0x23b3
    ret
"""
    transformed = """
; independent comment before origin
.org 0x1000

_start:
    ; comment before instruction
    mov [0xc03a], 0x23b3

    ret
; trailing comment
"""
    original = _assemble(baseline, tmp_path / "original.bin", tmp_path)
    variant = _assemble(transformed, tmp_path / "variant.bin", tmp_path)
    assert original == variant
    assert original, "empty machine-code output cannot qualify equivalence"


def test_negative_control_changes_immediate(tmp_path):
    original = _assemble(
        ".org 0x1000\n_start:\n mov [0xc03a], 0x23b3\n ret\n",
        tmp_path / "original.bin", tmp_path,
    )
    changed = _assemble(
        ".org 0x1000\n_start:\n mov [0xc03a], 0x23b2\n ret\n",
        tmp_path / "changed.bin", tmp_path,
    )
    assert original != changed, "negative control failed to detect altered operand"
