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

## Current project state

For mutable integration status, use root `CLAUDE.md`, `docs/AGENT_HANDOFF.md`,
and GitHub issue #8 rather than an old README commit snapshot. The developer
and container environment contract is `docs/CONTAINER_STRATEGY.md`.

## Portable quick start

The canonical project environment is containerized. A new Windows, Linux, or
macOS source host needs Git, Python 3.10+, and a supported Docker-compatible
runtime; GitHub CLI is also required for the local-agent handoff workflow.

Windows PowerShell:

```powershell
.\scripts\dev.ps1 doctor
.\scripts\dev.ps1 bootstrap
.\scripts\dev.ps1 tool cy16-as examples/setup_stub.s -o build/setup_stub.bin --base 0x1000 --lst build/setup_stub.lst --map build/setup_stub.map
.\scripts\dev.ps1 tool cy16-dis build/setup_stub.bin --base 0x1000
.\scripts\dev.ps1 tool cy16-sim build/setup_stub.bin --base 0x1000 --pc 0x1000 --max-steps 4
```

Linux/macOS POSIX shell:

```bash
./scripts/dev.sh doctor
./scripts/dev.sh bootstrap
./scripts/dev.sh tool cy16-as examples/setup_stub.s -o build/setup_stub.bin --base 0x1000 --lst build/setup_stub.lst --map build/setup_stub.map
./scripts/dev.sh tool cy16-dis build/setup_stub.bin --base 0x1000
./scripts/dev.sh tool cy16-sim build/setup_stub.bin --base 0x1000 --pc 0x1000 --max-steps 4
```

`bootstrap` builds the isolated Docker `test` target and then the minimal runtime
image. Runtime commands use a read-only repository mount, a writable `build/`
submount, no network, a read-only container root, dropped capabilities, and
`--rm`; no background or persistent container is required.

Linux Docker execution is validated end-to-end on native `amd64` and native
`arm64` runners. Windows and macOS launcher and diagnostic surfaces are
validated on hosted runners; Docker Desktop project-container execution on those
hosts remains a local-machine validation gate.

The compiled chibicc-derived binary is exposed separately as `cy16-chibicc`.
The Python project compiler remains `cy16-cc`; the two names must not overwrite
each other.

### Optional native Python path

A native venv is still useful for Python-only iteration:

```bash
python -m venv .venv
# Linux/macOS: . .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -e . pytest pycparser
pytest -q
```

A full native compiler validation also requires a compatible C compiler and
`make`, so the container path is preferred when moving among development
machines.

A hosted Mac validates the POSIX/Python project launcher, and native Linux ARM64
validation covers the same project toolchain architecture used by Apple Silicon
containers. No separate macOS toolchain is planned; the remaining Mac-specific
work is Docker Desktop/runtime and volume behavior on an actual development Mac.

## Package contents

- `docs/CITED_FINDINGS.md` — research findings with source references.
- `docs/POAM.md` — plan of action and milestones for the chibicc-based CY16 compiler.
- `docs/ARCHITECTURE.md` — proposed project architecture.
- `docs/ABI_V0.md` — initial CY16 C ABI.
- `docs/ASM_SUBSET.md` — bootstrap assembler syntax and limitations.
- `docs/SCAN_FORMAT.md` — SCAN record model.
- `docs/CONTAINER_STRATEGY.md` — cross-platform DX and stateless/minimal container contract.
- `prompts/AGENT_BOOTSTRAP_PROMPT.md` — one-shot prompt for Codex CLI, Gemini CLI, or Jules.
- `src/cy16boot/` — bootstrap Python tools.
- `src/cy16cc/` — chibicc-derived compiler port and CY16 backend.
- `libcy16/` — startup/runtime/linker-script seed files.
- `scripts/dev.py` — portable cross-platform host wrapper.
- `scripts/vendor_chibicc.sh` — pins and vendors chibicc.
- `tests/` — pytest tests.

## Important license/IP note

This package contains original bootstrap code and documentation summaries. It does not include Cypress proprietary documentation text or old GNUPro source. If you vendor chibicc, preserve its MIT license. If you import GPL Linux-driver code or headers, isolate it and keep the resulting licensing implications explicit.
