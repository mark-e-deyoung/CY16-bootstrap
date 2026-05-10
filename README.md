# CY16 Compiler Bootstrap Kit

This package bootstraps a CY16 assembler/compiler project based on the recommended path:

1. Build a trustworthy assembler, disassembler, simulator, and SCAN tools.
2. Vendor a pinned MIT-licensed chibicc commit as the frontend seed.
3. Replace chibicc's x86-64 backend with a CY16 backend that emits CY16 assembly.
4. Validate all compiler output through `cy16-as`, `cy16-dis`, `cy16-sim`, and `cy16-scanwrap`.

This is a bootstrap package, not a finished CY16 compiler. The included Python tools are complete enough to build, test, and validate the known Cypress `scanwrap.c` setup-stub encoding:

```asm
.org 0x1000
_start:
    mov [0xc03a], 0x23b3
    ret
```

Expected CY16 words:

```text
0x07e7 0x23b3 0xc03a 0xcf97
```

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows PowerShell equivalent
pip install -e . pytest
pytest -q

cy16-as examples/setup_stub.s -o build/setup_stub.bin --base 0x1000 --lst build/setup_stub.lst --map build/setup_stub.map
cy16-dis build/setup_stub.bin --base 0x1000
cy16-sim build/setup_stub.bin --base 0x1000 --pc 0x1000 --max-steps 4
cy16-scanwrap build/setup_stub.bin build/setup_stub.scan 0x1000
cy16-scan-decode build/setup_stub.scan
```

## Package contents

- `docs/CITED_FINDINGS.md` — research findings with source references.
- `docs/POAM.md` — plan of action and milestones for the chibicc-based CY16 compiler.
- `docs/ARCHITECTURE.md` — proposed project architecture.
- `docs/ABI_V0.md` — initial CY16 C ABI.
- `docs/ASM_SUBSET.md` — bootstrap assembler syntax and limitations.
- `docs/SCAN_FORMAT.md` — SCAN record model.
- `prompts/AGENT_BOOTSTRAP_PROMPT.md` — one-shot prompt for Codex CLI, Gemini CLI, or Jules.
- `src/cy16boot/` — bootstrap Python tools.
- `src/cy16cc/` — placeholder for the eventual chibicc-derived compiler port.
- `libcy16/` — startup/runtime/linker-script seed files.
- `scripts/vendor_chibicc.sh` — pins and vendors chibicc.
- `tests/` — pytest tests.

## Important license/IP note

This package contains original bootstrap code and documentation summaries. It does not include Cypress proprietary documentation text or old GNUPro source. If you vendor chibicc, preserve its MIT license. If you import GPL Linux-driver code or headers, isolate it and keep the resulting licensing implications explicit.
