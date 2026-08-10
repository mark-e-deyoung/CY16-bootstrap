# CY16 ISA conformance matrix

This matrix separates questions that are otherwise easy to conflate:

1. Is the behavior documented by the Programmer's Guide?
2. Can the assembler encode it and reject illegal operands?
3. Can the disassembler recover an equivalent instruction?
4. Can the simulator execute the documented state transition?
5. May the compiler backend safely emit it?

`Baseline` means support exists and is exercised in the project test ladder. `Partial` means a useful subset exists but important forms remain absent. `Audit` means code exists but dedicated source-derived tests remain incomplete. `Planned` means the feature must not be treated as implemented.

## Instruction families

| Family | Documented | Assembler | Disassembler | Simulator | Compiler emission | Current evidence / next work |
|---|---:|---|---|---|---|---|
| `MOV` register/immediate/direct/indirect word | Yes | Baseline | Baseline | Baseline | Baseline | flags-preservation and R15 push/pop tests added; byte/indexed modes remain |
| `ADD`, `SUB`, `CMP` | Yes | Baseline | Baseline | Baseline | Baseline subset | expand overflow and memory-operand vectors |
| `ADDC`, `SUBB` | Yes | Baseline | Baseline | Baseline | Backend-dependent | carry/borrow execution fixed and tested on research branch |
| `AND`, `TEST`, `OR`, `XOR` | Yes | Baseline | Baseline | Baseline | Baseline subset | Z/S update and C/O preservation test added for logical operation |
| Conditional relative jump | Yes | Planned | Planned | Planned | Planned | assembler currently emits absolute form only; implement signed seven-bit word displacement |
| Conditional absolute jump | Yes | Baseline | Baseline | Baseline | Baseline | add explicit condition-false and register-target tests |
| Assembler short/long auto-selection | Yes | Planned | Planned | N/A | Planned | requires relative form before range promotion can exist |
| `CALL` and conditional calls | Yes | Baseline | Baseline | Baseline | Baseline | add nested calls and condition-false stack-preservation test |
| `RET` | Yes | Baseline | Baseline | Baseline | Baseline | stack restore behavior present; add conditional-return variants |
| Conditional return mnemonics | Yes | Planned/partial | Partial | Conditional engine exists | Planned | RET word is supported; general conditional RET syntax/encoding needs implementation |
| `INT` | Yes | Planned | Planned | Planned | Planned for BIOS wrappers | vector-times-two and return-stack semantics not yet implemented |
| `SHR`, `SHL`, `ROR`, `ROL` | Yes | Baseline | Baseline | Baseline | Baseline subset | sign-extending SHR, rotate, carry, Z/S semantics corrected and tested |
| `ADDI`, `SUBI` | Yes | Baseline | Baseline | Baseline | Baseline | values 1-8 and Z/S-only flag behavior tested |
| `NOT`, `NEG`, `CBW` | Yes | Planned | Planned | Planned | Planned | implement seven-bit special-op encodings and edge-value tests |
| `STI`, `CLI`, `STC`, `CLC` | Yes | Planned | Planned | Planned | Planned runtime use | add interrupt/carry flag model; `STI` has documented one-cycle delay |

## Addressing modes

| Mode | Source rule | Current status | Required conformance work |
|---|---|---|---|
| Register | R0-R15 operand | Baseline | encode/decode every register number |
| Immediate | source only | Partial | positive source use works; explicitly reject immediate destinations rather than failing later |
| Direct word | even-aligned word access | Baseline subset | define and test odd-address policy |
| Direct byte | byte-addressable memory; ALU remains 16-bit | Planned | low/high-byte selection, storage, and flags |
| Indirect word | R8-R15 pointer-capable; R15 special | Baseline subset | exhaustive R8-R14 tests and explicit R15 distinction |
| General indirect auto-increment | documented mode | Planned | encode/decode byte/word increments |
| Indirect with offset/index | unsigned 16-bit following word; wraps address space | Planned | parser, extension-word and wraparound tests |
| R15 indirect write | pre-decrement, then store | Baseline | exact stack pointer/memory test added |
| R15 indirect read | load, then post-increment | Baseline | exact value/stack pointer test added |
| R15 byte indirect | prohibited | Not representable yet | retain a negative test when byte syntax is added |
| R15 indexed | no automatic increment/decrement | Planned | pointer-unchanged test |

## Completed source-derived corrections on the research branch

- `MOV` no longer changes flags.
- `ADDC` now consumes carry-in and calculates arithmetic flags.
- `SUBB` now consumes borrow-in and calculates arithmetic flags.
- Logical operations update Z/S while preserving C/O.
- `SHR` now sign-extends rather than shifting in zeros.
- `SHL`, `SHR`, `ROR`, and `ROL` set carry from the last bit shifted or rotated out.
- `ROR` and `ROL` now perform actual rotation.
- `ADDI` and `SUBI` update only Z/S and preserve C/O.
- Counts 1-8 are tested against the documented `count - 1` encoding.
- R15 push/pop word behavior has a simulator test.

These changes are not a new green baseline until pull-request CI passes.

## Control-flow implementation target

The Programmer's Guide defines short jumps as a signed seven-bit displacement multiplied by two. Once relative encoding is implemented, require:

| Case | Expected result |
|---|---|
| displacement `-64` | encodes as short |
| displacement `+63` | encodes as short |
| displacement `-65` | auto-promotes to long, or errors under explicit-short syntax |
| displacement `+64` | auto-promotes to long, or errors under explicit-short syntax |
| explicit short outside range | hard error |
| odd-byte target | hard error because the displacement is word-scaled |

Until then, documentation and tests must not describe ordinary `jmp` as relative; the current assembler uses the absolute destination form.

## Stack and interrupt semantics

Implemented/tested:

- stack grows toward lower addresses for R15 writes;
- R15 pre-decrements before a stack store;
- R15 post-increments after a stack read;
- ordinary CALL/RET linkage exists in the simulator.

Still required:

- nested calls with local stack use;
- conditional CALL/RET behavior;
- `INT v` pushes a return address and loads PC from memory at `v * 2`;
- hardware ISR flag/register preservation;
- interrupt-enable state and delayed `STI` effect.

## Assembler macros

The historical assembler defines these as macros, not independent CPU opcodes:

| Source macro | Canonical expansion | Status |
|---|---|---|
| `INC X` | `ADDI X, 1` | Planned parser compatibility |
| `DEC X` | `SUBI X, 1` | Planned parser compatibility |
| `PUSH X` | `MOV [R15], X` | Canonical stack form works; macro spelling planned |
| `POP X` | `MOV X, [R15]` | Canonical stack form works; macro spelling planned |

The simulator should execute only the expanded instruction; macro support belongs in the assembler/parser layer.

## Compiler safety gates

The backend may emit an instruction/addressing mode only when:

1. the assembler has a positive encoding test;
2. the disassembler has a round-trip test;
3. the simulator has a state and documented-flag test;
4. illegal edge cases have negative tests;
5. the ABI documents register and stack effects.

Volatile MMIO tests remain separate from DE2-115 HPI access rules: internally executing CY16 code can access processor-control registers such as `0xC004`, while an external HPI master has a narrower direct-access map.

## Next implementation order

1. Run CI for the corrected arithmetic/shift/rotate semantics and new fixtures.
2. Add explicit immediate-destination and odd-word-address diagnostics.
3. Implement relative jumps and short/long selection with boundary tests.
4. Implement `INT` and conditional RET forms.
5. Implement `NOT`, `NEG`, and `CBW`.
6. Add carry/interrupt-control instructions and delayed `STI` behavior.
7. Add byte and indexed addressing.
8. Add historical macro spellings.
9. Add cycle accounting only if simulator timing becomes a project requirement.
