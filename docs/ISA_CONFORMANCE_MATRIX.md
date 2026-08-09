# CY16 ISA conformance matrix

This matrix separates four questions that are otherwise easy to conflate:

1. Is the behavior documented by the Programmer's Guide?
2. Can the assembler encode it and reject illegal operands?
3. Can the disassembler recover an equivalent instruction?
4. Can the simulator execute the documented state transition?
5. May the compiler backend safely emit it?

`Baseline` means support exists in the current project and is exercised somewhere in the test ladder. `Audit` means code appears to support the feature, but a dedicated source-derived boundary/semantic test is still required. `Planned` means the feature should not be treated as conformant yet.

## Instruction families

| Family | Documented | Assembler | Disassembler | Simulator | Compiler emission | Priority test work |
|---|---:|---|---|---|---|---|
| `MOV` register/immediate/direct/indirect | Yes | Baseline | Baseline | Baseline | Baseline | exhaustive addressing-mode legality and byte/word cases |
| `ADD`, `ADDC`, `SUB`, `SUBB`, `CMP` | Yes | Baseline | Baseline | Baseline | Baseline subset | dedicated carry, borrow, overflow, sign, and zero vectors |
| `AND`, `TEST`, `OR`, `XOR` | Yes | Baseline | Baseline | Baseline | Baseline subset | flag preservation/updates and memory operands |
| Conditional relative jump | Yes | Baseline | Baseline | Baseline | Baseline | exact `-64` and `+63` word-displacement boundaries |
| Conditional absolute jump | Yes | Baseline | Baseline | Baseline | Baseline | relocation/symbol target and explicit long form |
| Assembler short/long auto-selection | Yes | Audit | Audit | N/A | Indirect | promotion at `-65`/`+64`; explicit-short failure |
| `CALL` and conditional calls | Yes | Baseline | Baseline | Baseline | Baseline | pushed return address and nested calls |
| `RET` and conditional returns | Yes | Baseline | Baseline | Baseline | Baseline | R15 increment and condition-false behavior |
| `INT` | Yes | Audit | Audit | Audit | Planned for BIOS wrappers | vector multiplied by two, return-address stack behavior |
| `SHR`, `SHL`, `ROR`, `ROL` | Yes | Baseline | Baseline | Baseline | Baseline subset | all counts 1-8 and `count - 1` encoding |
| `ADDI`, `SUBI` | Yes | Baseline | Baseline | Baseline | Baseline | all immediates 1-8 and flag semantics |
| `NOT`, `NEG`, `CBW` | Yes | Audit | Audit | Audit | Backend-dependent | edge vectors including `0x0000`, `0x8000`, byte sign extension |
| `STI`, `CLI`, `STC`, `CLC` | Yes | Audit | Audit | Audit | Planned runtime use | delayed `STI` effect and exact flag changes |

## Addressing modes

| Mode | Source rule | Current status | Required conformance test |
|---|---|---|---|
| Register | R0-R15 operand | Baseline | encode/decode every register number |
| Immediate | source only | Baseline | assembler rejects immediate destination |
| Direct word | even-aligned word access | Baseline | odd word address rejected or deliberately handled according to tool policy |
| Direct byte | byte-addressable memory; ALU remains 16-bit | Audit | low/high-byte selection and flag behavior |
| Indirect | R8-R15 pointer-capable; R15 special | Baseline subset | legal-register validation and R15 semantics |
| Indirect auto-increment | documented mode; R15 restrictions | Audit | pointer increments by byte/word width; illegal R15 byte form |
| Indirect with offset/index | unsigned 16-bit following word; wraps address space | Audit | positive wraparound and instruction-length handling |
| R15 indirect write | pre-decrement, then store | Baseline stack forms | exact new SP and memory address |
| R15 indirect read | load, then post-increment | Baseline stack forms | exact loaded value and new SP |
| R15 byte indirect | prohibited | Audit | assembler/compiler rejection |
| R15 indexed | no automatic increment/decrement | Audit | pointer remains unchanged |

## Control-flow boundaries

The Programmer's Guide defines short jumps as a signed seven-bit displacement multiplied by two. Add exact tests for:

| Case | Expected result |
|---|---|
| displacement `-64` | encodes as short |
| displacement `+63` | encodes as short |
| displacement `-65` | auto-promotes to long or explicit diagnostic according to syntax |
| displacement `+64` | auto-promotes to long or explicit diagnostic according to syntax |
| explicit short outside range | hard error |
| odd-byte target | hard error because the encoded displacement is word-scaled |

## Shift/small-immediate encoding

For `SHR`, `SHL`, `ROR`, `ROL`, `ADDI`, and `SUBI`, the encoded three-bit field stores `n - 1`. The conformance suite must test source operands 1 through 8 and reject zero or values above eight unless an explicitly documented assembler extension lowers them into multiple instructions.

## Stack and interrupt semantics

Required simulator tests:

- stack grows toward lower addresses;
- `MOV [R15], X` performs pre-decrement before the store;
- `MOV X, [R15]` reads before post-increment;
- `CALL` pushes the next instruction address;
- `INT v` pushes the return address and loads PC from memory at `v * 2`;
- `RET` restores PC and increments R15;
- hardware ISR template preserves flags/registers and ends with `STI`/`RET` only after delayed-interrupt behavior is modeled.

## Assembler macros

The historical assembler defines these as macros, not distinct CPU opcodes:

| Source macro | Canonical expansion | Status |
|---|---|---|
| `INC X` | `ADDI X, 1` | Planned dedicated parser/round-trip test |
| `DEC X` | `SUBI X, 1` | Planned dedicated parser/round-trip test |
| `PUSH X` | `MOV [R15], X` | Stack syntax baseline; macro spelling audit |
| `POP X` | `MOV X, [R15]` | Stack syntax baseline; macro spelling audit |

The simulator should execute only the expanded instruction; macro support belongs in the assembler/parser layer.

## Compiler safety gates

The backend may emit an instruction/addressing mode only when:

1. the assembler has a positive encoding test;
2. the disassembler has a round-trip test;
3. the simulator has a state/flag test;
4. illegal edge cases have negative tests;
5. the ABI documents register and stack effects.

Volatile MMIO tests must remain separate from DE2-115 HPI access rules: a CY16 program executing internally can access processor-control registers such as `0xC004`, while an external HPI master cannot necessarily access that same location directly.

## Next implementation order

1. Branch range and auto-selection boundaries.
2. Shift/rotate/small-immediate counts 1-8.
3. R15 pre-decrement/post-increment and illegal byte forms.
4. `INT` vector-table and return behavior.
5. `NOT`/`NEG`/`CBW` flags and edge values.
6. Flag-control instructions, including delayed `STI` effect.
7. Byte and indexed addressing.
8. Historical macro spellings.
9. Cycle-count accounting, if simulator timing becomes a project requirement.
