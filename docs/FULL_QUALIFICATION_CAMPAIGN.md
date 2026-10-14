# CY16 compiler and emulator qualification campaign

Status: qualification plan and evidence contract, **not a pass declaration**.
Authority: docs/POAM.md, docs/CY16_SPEC_RECONCILIATION.md,
docs/CY16_PRIMARY_SOURCE_BATCH2.md, docs/QUALIFICATION_EXECUTION_POLICY.md.

## Target deliverables and acceptance

**Simulator / emulator**: documented CY16 instruction decoding,
operand legality, ALU/flags, memory/register windows, stack/calls,
interrupt/reset behavior, and separately selected EZ-OTG/EZ-Host BIOS
profiles. Unspecified silicon behavior remains explicitly unknown.
Device emulation requires validated peripherals and host/HPI behavior;
a CPU interpreter alone is not a complete board emulator.

**Compiler**: specified C dialect and ABI, reproducible source-to-image
pipeline, correct calls/stack/register preservation, data layout,
volatile accesses, sections/linking, diagnostics, and supported
language constructs. Historical GNUPro binary compatibility is a
separate gate, not inferred from project ABI v0.

## Critical path: independent oracles before mutual validation

1. **Evidence closure:** pin original source versions/hashes and
   chip/BIOS applicability; reconcile instruction tables, mode encodings,
   flags, reset, interrupts, and memory map with page-level provenance.
2. **Instruction oracle:** source-derived encodings/decodings with
   positive, illegal, boundary and metamorphic vectors. Test assembler
   against independent bytes; round-trip alone is insufficient.
3. **CPU model:** implement opt-in RAM-backed registers, FLAGS and
   REGBANK MMIO with strict red tests; retain flat mode unchanged.
   Qualify arithmetic, carry/borrow, branches, CALL/RET, stack,
   wraparound and byte-vs-word behavior against independent expectations.
4. **Device profiles:** EZ-OTG vs EZ-Host memory, BIOS ROM, vectors,
   paged windows and peripheral stubs. Unmodeled MMIO must be explicit;
   do not silently return plausible values.
5. **Compiler ABI:** define stack frame, parameter passing, register
   preservation, static/global initialization and volatile semantics;
   source-vetted ABI versus project-defined ABI separately.
6. **Compiler correctness:** C source fixtures with independently
   computed results; compare against a qualified reference C model
   when types/overflow permit; run generated binaries on qualified
   emulator, then device.
7. **Hardware witness:** only after S04 HPI RAM safety gate, use
   bounded readback and reversible hardware-in-loop probes. Archive
   binary hashes, trace, chip revision, BIOS revision and observations.
8. **Release gate:** reproducible clean-room builds, documented
   supported/unsupported surface, test coverage matrix, failures,
   independent reproducer and provenance; no unqualified 'fully
   compatible' claim.

## Execution and cost boundaries

- Public CY16 source and non-sensitive tests: public repository
  GitHub Actions under the public-repo allowance, subject to live
  workflow verification.
- Private source documents, proprietary evidence and private tests:
  Agent Dispatch qualified executor only. Do not consume private
  GitHub-hosted Actions minutes in either execution or dispatch.
- Runtime provenance must identify public/self-hosted/other,
  dispatcher, repository visibility, revision and artifact digest.
- No private evidence may be uploaded into public CI logs/artifacts.

## Parallel work versus serial dependencies

Parallel now: evidence indexing, opcode oracle vectors, compiler
language/ABI coverage inventory, device memory-map inventory, runtime
availability checks. Serial: architectural emulator changes follow
source-backed red tests; compiler-vs-emulator qualification follows
independent oracle checks; physical HIL follows S04 safety approval.

## Evidence ledger required for every gate

`gate | claim | source/version/page | target chip/BIOS |
test/negative control | execution shape | commit/artifact SHA |
observed result | reviewer | status (pass/fail/blocked/unknown)`

A green CI badge alone is not sufficient for full qualification.
