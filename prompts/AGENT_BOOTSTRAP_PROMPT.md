# Agent bootstrap prompt for Codex CLI / Gemini CLI / Google Jules

You are working in a repository generated from the CY16 Compiler Bootstrap Kit. Your mission is to turn this bootstrap into a real CY16 C compiler project using chibicc as the frontend seed and a custom CY16 backend.

## Non-negotiable goals

1. Preserve the validation ladder:
   ```text
   C -> CY16 assembly -> cy16-as -> cy16-dis -> cy16-sim -> cy16-scanwrap -> cy16-scan-decode
   ```
2. Do not start with LLVM or GCC.
3. Do not emit ELF in v0. Emit assembly first.
4. Do not copy Cypress proprietary tables/source into the project. Use the docs as references and summarize facts.
5. Preserve chibicc's MIT license if/when vendored.
6. Keep every change testable with `pytest` or a clear build/test command.
7. Make PR-sized changes; do not do large unreviewable rewrites.

## Current bootstrap state

The repository already includes:

- `cy16-as`: tiny assembler anchored on the Cypress scanwrap setup-stub fixture.
- `cy16-dis`: tiny disassembler for the same fixture.
- `cy16-sim`: tiny simulator for the same fixture.
- `cy16-scan-decode`: SCAN record decoder.
- `cy16-scanwrap`: SCAN wrapper.
- `cy16-cc-mini`: placeholder smoke compiler, not the final compiler.
- docs and tests.

## First milestone

Expand the assembler and disassembler while keeping the golden test intact.

### Tasks

1. Add a data-driven ISA representation under `src/cy16boot/isa.py`.
2. Implement these instruction forms with tests:
   - `ret`
   - `mov [addr], imm` (already present; refactor, do not break)
   - `mov rN, imm`
   - `mov rN, [addr]`
   - `mov [addr], rN`
3. Add tests for directives:
   - `.org`
   - `.equ`
   - `.word`/`.short`
   - `.byte`
4. Add round-trip tests:
   ```text
   assembly -> binary -> disassembly -> assembly-like equivalent
   ```
5. Keep this command passing:
   ```bash
   pytest -q
   ```

## Second milestone

Make `cy16-sim` run simple register and memory tests.

### Tasks

1. Add register state R0-R15.
2. Implement load/store forms added in milestone 1.
3. Add CLI options to initialize registers and dump registers.
4. Add simulator tests for memory-mapped writes and reads.

## Third milestone

Vendor chibicc and make the frontend build.

### Tasks

1. Run or adapt `scripts/vendor_chibicc.sh`.
2. Preserve upstream LICENSE and commit hash.
3. Create `src/cy16cc` build skeleton.
4. Add a `cy16-cc --version` and `cy16-cc -fsyntax-only` mode.
5. Disable unsupported constructs clearly.

## Fourth milestone

Add CY16 IR and backend v0.

### v0 C subset

Support:

```c
uint8_t
int8_t
uint16_t
int16_t
pointers
globals
locals
if/else
while/for
function calls
volatile loads/stores
```

Skip:

```text
float/double
long long
varargs
malloc/full libc
structs by value
ELF output
debug info
interrupt handlers
```

### Required generated-code tests

1. `uint16_t add(uint16_t a, uint16_t b) { return a + b; }`
2. `uint16_t read_hwrev(void) { return *(volatile uint16_t *)0xC004; }`
3. A loop accumulating a sum.
4. A function call test.
5. A global variable load/store test.

Each test must compile to assembly, assemble, simulate, and assert expected state.

## Suggested commit order

1. `docs: preserve CY16 research findings and compiler POAM`
2. `tooling: add data-driven CY16 ISA scaffold`
3. `assembler: implement core mov forms and tests`
4. `sim: execute core mov forms and register dumps`
5. `third_party: vendor pinned chibicc upstream`
6. `compiler: add cy16 target config and syntax-only mode`
7. `compiler: add CY16 IR dump for v0 subset`
8. `compiler: emit CY16 assembly for leaf functions`
9. `runtime: add minimal headers and startup variants`
10. `examples: build SCAN-wrapped CY16 test programs`

## Acceptance gate for every PR

```bash
pytest -q
python -m cy16boot.asm examples/setup_stub.s -o build/setup_stub.bin --base 0x1000 --lst build/setup_stub.lst --map build/setup_stub.map
python -m cy16boot.dis build/setup_stub.bin --base 0x1000
python -m cy16boot.sim build/setup_stub.bin --base 0x1000 --pc 0x1000 --dump 0xc03a
python -m cy16boot.scan build/setup_stub.scan || true
```

Replace the last line with the proper console script once installed:

```bash
cy16-scanwrap build/setup_stub.bin build/setup_stub.scan 0x1000
cy16-scan-decode build/setup_stub.scan
```
