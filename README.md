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

## Current status

`main` remains the last recorded green integration baseline at commit `50e642a` from 2026-05-11.

The current research/conformance branch adds:

- a source and provenance index;
- an ISA conformance matrix and priority test plan;
- a clean-room AN048 end-to-end fixture;
- decoding/tests for documented SCAN opcode `0x09` (`WRITE_CONFIG`);
- a CY3663/Xilinx artifact-recovery catalog and 2026-08-09 search log;
- pinned notes for Linux `c67x00`, the UIUC DE2-115 example, and Stierlitz.

These changes must pass pull-request CI before they become the new green baseline.

- Local Docker validation command: `docker build -t cy16-ladder .`
- Last recorded green local result on the prior baseline: `23 passed`
- Last recorded green GitHub Actions run on the prior baseline: `25679773430`
- Current handoff notes: `HANDOFF.md`
- Bring-up sequencing and delegation plan: `docs/ORCHESTRATION_PLAN.md`

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

### Research and compatibility

- `docs/SOURCE_INDEX.md` — provenance, pinned references, and source-to-test mapping.
- `docs/CITED_FINDINGS.md` — technical findings and design implications.
- `docs/ISA_CONFORMANCE_MATRIX.md` — instruction/addressing support and priority gaps.
- `docs/AN048_BAL_COMPATIBILITY.md` — historical workflow and clean-room acceptance target.
- `docs/CY3663_ARTIFACT_WANTED.md` — exact legacy targets and search log.
- `docs/EXTERNAL_IMPLEMENTATION_NOTES.md` — Linux, UIUC, Stierlitz, CY4640, and Xilinx analysis.
- `fixtures/an048-bal/` — clean-room AN048-shaped C/startup fixture.

### Architecture and implementation

- `docs/POAM.md` — plan of action and milestones for the chibicc-based CY16 compiler.
- `docs/ARCHITECTURE.md` — proposed project architecture.
- `docs/ABI_V0.md` — initial CY16 C ABI.
- `docs/ASM_SUBSET.md` — bootstrap assembler syntax and limitations.
- `docs/SCAN_FORMAT.md` — SCAN record model, including configuration writes.
- `prompts/AGENT_BOOTSTRAP_PROMPT.md` — one-shot prompt for Codex CLI, Gemini CLI, or Jules.
- `src/cy16boot/` — bootstrap Python tools.
- `src/cy16cc/` — chibicc-derived compiler port and CY16 backend.
- `libcy16/` — startup/runtime/linker-script seed files.
- `scripts/vendor_chibicc.sh` — pins and vendors chibicc.
- `tests/` — pytest tests, including AN048 and SCAN configuration fixtures.

## Companion hardware project

`SemperSupra/DE2-115` owns FPGA HPI timing, BIOS/LCP communication, SCAN execution, and USB-host bring-up. The compiler project produces images for that loader, but it does not treat external HPI accessibility as identical to CY16 internal MMIO access.

Hardware deployment remains gated on:

1. internal-RAM write/read over HPI;
2. `COMM_RESET` returning `COMM_ACK`;
3. SCAN COPY readback verification;
4. verified control-register translation and CALL/JUMP behavior.

## Important license/IP note

This package contains original bootstrap code and documentation summaries. It does not include old GNUPro source. Cypress/Infineon documents and source-derived artifacts must be handled according to their licenses; public availability does not imply permission to relicense them. Preserve the chibicc MIT license. Keep GPL Linux/Stierlitz code behind explicit license boundaries or use it only as a behavioral reference.
