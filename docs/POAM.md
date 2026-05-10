# CY16 chibicc-based compiler POAM

## Objective

Implement a CY16 C compiler by using chibicc as a frontend seed and replacing its x86-64 backend with a CY16 backend that emits CY16 assembly. Validate every stage through project-owned assembler, disassembler, simulator, and SCAN tools.

## Phase 0: Repository and legal foundation

Deliverables:

- Repository scaffold.
- MIT license for original bootstrap code.
- chibicc vendoring script and upstream license preservation.
- `docs/CITED_FINDINGS.md` and `docs/legal-notes.md`.

Exit criteria:

- Project builds with `pip install -e .`.
- Test suite runs.
- License/source boundaries are documented.

## Phase 1: Bootstrap assembler/disassembler/SCAN tools

Deliverables:

- `cy16-as`
- `cy16-dis`
- `cy16-scan-decode`
- `cy16-scanwrap`
- Golden tests for `scanwrap.c` setup stub.

Exit criteria:

- `mov [0xc03a], 0x23b3 ; ret` assembles to `0x07e7 0x23b3 0xc03a 0xcf97`.
- The binary disassembles back to equivalent assembly.
- Wrapped SCAN image decodes cleanly.

## Phase 2: Simulator MVP

Deliverables:

- `cy16-sim`
- CPU state with 64 KiB memory, R0-R15, PC, flags placeholders.
- Execution of bootstrap instruction subset.
- Trace output and memory dump assertions.

Exit criteria:

- The setup-stub binary writes `0x23b3` to `0xc03a` and halts at `ret`.

## Phase 3: ABI v0 and runtime profiles

Deliverables:

- `docs/ABI_V0.md`
- `libcy16/startup_bios.s`
- `libcy16/startup_nobios.s`
- `libcy16/startup_sim.s`
- linker-script seeds.

Exit criteria:

- Startup files assemble once the assembler supports their instruction subset.
- ABI decisions are stable enough for backend implementation.

## Phase 4: Vendor and trim chibicc frontend

Deliverables:

- Pinned upstream commit under `third_party/chibicc-upstream`.
- `src/cy16cc` frontend port.
- Unsupported features disabled with clear diagnostics.

Exit criteria:

- `cy16-cc -fsyntax-only` works for the v0 C subset.
- Unsupported features fail intentionally.

## Phase 5: CY16 IR

Deliverables:

- `cy16_ir.[ch]`
- AST-to-IR lowering.
- IR dump mode.

Exit criteria:

- Constants, arithmetic, branches, calls, loads/stores, and volatile MMIO lower to explicit CY16 IR.

## Phase 6: CY16 assembly backend v0

Deliverables:

- `cy16_codegen.[ch]`
- `cy16_regalloc.[ch]`
- `cy16_emit.[ch]`
- Stack-frame generation for simple functions.
- Assembly emission.

Exit criteria:

- C functions compile to assembly.
- Generated assembly assembles and runs in simulator.
- Arithmetic, branch, call, local, global, pointer, and volatile tests pass.

## Phase 7: Minimal headers and libcy16

Deliverables:

- `include/stdint.h`
- `include/stddef.h`
- `include/stdbool.h`
- `include/cy16.h`
- `include/cy7c67200.h`
- Minimal `memcpy`, `memset`, `memcmp`.

Exit criteria:

- Small embedded C examples compile without hosted libc.

## Phase 8: SCAN/HPI/DE2-115 examples

Deliverables:

- `examples/c/read_hwrev.c`
- `examples/c/write_memctl.c`
- `examples/c/bios_cooperative_main.c`
- `docs/DE2_115_INTEGRATION.md`

Exit criteria:

- Examples build to `.s`, `.bin`, `.scan`.
- SCAN decoder validates images.
- Integration doc explains how to hand images to the DE2-115 HPI loader path.

## Phase 9: v1 compiler features

Feature order:

1. Structs as memory objects.
2. Arrays and pointer arithmetic.
3. Switch/case.
4. Static locals.
5. Function pointers.
6. Interrupt attribute.
7. Inline assembly.
8. Peephole optimization.

Exit criteria:

- Each feature has simulator-backed tests.
- Volatile MMIO semantics remain correct.

## Phase 10: GNUPro compatibility convergence

Deliverables:

- More GNU assembler compatibility.
- More objdump/listing compatibility.
- Optional relocatable object format.
- Optional ELF/BFD exploration.
- Historical CY16 GCC/binutils archaeology if source patches are found.

Exit criteria:

- Historical Cypress-style examples assemble with minimal edits.
- SCAN deployment remains working.
