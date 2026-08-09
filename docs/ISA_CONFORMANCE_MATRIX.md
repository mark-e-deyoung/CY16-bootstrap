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
| `MOV` register/immediate/direct/indirect word | Yes | Baseline | Baseline | Baseline | Baseline | flags-preservation and R15 push/pop tests exist; byte/indexed modes remain |
| `ADD`, `SUB`, `CMP` | Yes | Baseline | Baseline | Baseline | Baseline subset | expand overflow and memory-operand vectors |
| `ADDC`, `SUBB` | Yes | Baseline | Baseline | Baseline | Backend-dependent | carry/borrow execution fixed and tested |
| `AND`, `TEST`, `OR`, `XOR` | Yes | Baseline | Baseline | Baseline | Baseline subset | Z/S update and C/O preservation tested |
| Conditional relative jump | Yes | Baseline | Baseline | Baseline | Audit | signed seven-bit word displacement, taken/not-taken, backward branch, and exact range boundaries tested |
| Conditional absolute jump | Yes | Baseline | Baseline | Baseline | Baseline | explicit long form and automatic promotion are tested; add register-target vectors |
| Assembler short/long auto-selection | Yes | Baseline | Baseline | N/A | Indirect | unsuffixed jumps relax iteratively; explicit short overflow and odd targets fail closed |
| `CALL` and conditional calls | Yes | Baseline | Baseline | Baseline | Baseline | add nested calls and condition-false stack-preservation tests |
| `RET` | Yes | Baseline | Baseline | Baseline | Baseline | stack restore behavior present; add conditional-return variants |
| Conditional return mnemonics | Yes | Planned/partial | Partial | Conditional engine exists | Planned | exact RET word works; general conditional RET syntax/encoding remains |
| `INT` | Yes | Baseline | Baseline | Baseline | Planned for BIOS wrappers | vector-times-two dispatch, return-address push, handler RET, and vector bounds tested |
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
| R15 indirect write | pre-decrement, then store | Baseline | exact stack pointer/memory tests include the `PUSH` macro |
| R15 indirect read | load, then post-increment | Baseline | exact value/stack pointer tests include the `POP` macro |
| R15 byte indirect | prohibited | Not representable yet | retain a negative test when byte syntax is added |
| R15 indexed | no automatic increment/decrement | Planned | pointer-unchanged test |

## Completed source-derived corrections

- `MOV` no longer changes flags.
- `ADDC` consumes carry-in and calculates arithmetic flags.
- `SUBB` consumes borrow-in and calculates arithmetic flags.
- Logical operations update Z/S while preserving C/O.
- `SHR` sign-extends rather than shifting in zeros.
- `SHL`, `SHR`, `ROR`, and `ROL` set carry from the last bit shifted or rotated out.
- `ROR` and `ROL` perform actual rotation.
- `ADDI` and `SUBI` update only Z/S and preserve C/O.
- Counts 1-8 are tested against the documented `count - 1` encoding.
- R15 push/pop word behavior has simulator tests.
- Relative jumps encode the documented signed seven-bit word offset.
- Explicit short and long jump forms are accepted, and unsuffixed jumps choose a stable form through iterative relaxation.
- Forced-short offsets `-64` and `+63` succeed; `-65`, `+64`, and odd-byte targets fail.
- Relative jumps execute in both taken and not-taken paths, including a backward loop.
- `INT` pushes the next instruction address, loads PC from `[vector * 2]`, and returns through ordinary `RET`.
- `INC`, `DEC`, `PUSH`, and `POP` expand to the documented real instructions.

GitHub Actions run `31324190788` completed the compiler build, full test suite, and direct control-flow tool exercise successfully for the stacked control-flow pull request.

## Control-flow behavior

The Programmer's Guide defines short jumps as a signed seven-bit displacement multiplied by two. The current implementation enforces:

| Case | Result |
|---|---|
| displacement `-64` | encodes as short |
| displacement `+63` | encodes as short |
| displacement `-65` | unsuffixed form promotes to long; explicit-short form errors |
| displacement `+64` | unsuffixed form promotes to long; explicit-short form errors |
| explicit short outside range | hard error |
| odd-byte target | hard error because the displacement is word-scaled |
| unsuffixed in-range target | relaxes to short |
| unsuffixed out-of-range target | remains/promotes to absolute long form |

The disassembler emits assembler-compatible `.s` and `.l` forms so decoded control flow can be reassembled without relying on presentation-only `if_*` syntax.

## Stack and interrupt semantics

Implemented/tested:

- stack grows toward lower addresses for R15 writes;
- R15 pre-decrements before a stack store;
- R15 post-increments after a stack read;
- ordinary CALL/RET linkage exists in the simulator;
- `INT v` decrements R15, stores the next instruction address, and loads PC from memory at `v * 2`;
- a handler ending in `RET` restores the interrupted instruction stream and R15.

Still required:

- nested calls with local stack use;
- conditional CALL/RET behavior;
- hardware ISR flag/register preservation;
- interrupt-enable state and delayed `STI` effect.

## Assembler macros

The historical assembler defines these as macros, not independent CPU opcodes:

| Source macro | Canonical expansion | Status |
|---|---|---|
| `INC X` | `ADDI X, 1` | Baseline; encoding-equivalence test |
| `DEC X` | `SUBI X, 1` | Baseline; encoding-equivalence test |
| `PUSH X` | `MOV [R15], X` | Baseline; encoding and stack-state test |
| `POP X` | `MOV X, [R15]` | Baseline; encoding and stack-state test |

The simulator executes only the expanded instruction. No pseudo-opcode was added.

## Compiler safety gates

The backend may emit an instruction/addressing mode only when:

1. the assembler has a positive encoding test;
2. the disassembler has a round-trip or equivalent-form test;
3. the simulator has a state and documented-flag test;
4. illegal edge cases have negative tests;
5. the ABI documents register and stack effects.

Volatile MMIO tests remain separate from DE2-115 HPI access rules: internally executing CY16 code can access processor-control registers such as `0xC004`, while an external HPI master has a narrower direct-access map.

## Next implementation order

1. Add explicit immediate-destination and odd-word-address diagnostics.
2. Implement conditional RET forms and condition-false CALL stack-preservation tests.
3. Implement `NOT`, `NEG`, and `CBW`.
4. Add carry/interrupt-control instructions and delayed `STI` behavior.
5. Add byte and indexed addressing.
6. Add nested-call and stack-local stress tests.
7. Add cycle accounting only if simulator timing becomes a project requirement.
