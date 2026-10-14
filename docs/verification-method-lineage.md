# CY16 verification methods: lineage, durability and bounded adoption

Status: **candidate methodology**, not an assertion of compiler or silicon conformance.
Authority: existing compiler POAM/HANDOFF and draft PR #39. No replacement architecture authorized.

| Primitive | Established lineage | Durable invariant | Bounded CY16 use | Failure mode / adoption gate |
|---|---|---|---|---|
| Differential testing | Compiler cross-checking; Csmith (2011) | Compare observable outcomes under independent implementations | Compare supported, defined-behavior C programs with host compiler and CY16 simulation | Target-specific widths/ABI invalidate naive comparisons; normalize explicitly |
| Metamorphic testing | Metamorphic testing (1990s); compiler EMI (2014) | Relate outcomes across semantics-preserving changes | Dead-code and controlled expression mutations | Only transformations proved valid under C semantics |
| Property-based testing | QuickCheck (2000) | Generate reproducible invariant-focused cases | Encoding/decoding, relocation and register-state properties | Seed and shrinker must be archived |
| ISA executable specifications | Architectural operational semantics; Sail | Separate normative behavior from implementations | Independent semantics for selected high-risk instructions | Do not import full Sail framework without demonstrated gain |
| Coverage-guided instruction generation | Constrained-random hardware verification; riscv-dv | Exercise state/operand/transition boundaries | CY16 opcode/flags/branch coverage bins | No RISC-V-specific framework dependency |
| Translation validation | Compiler-correctness research (1990s onward) | Validate outputs rather than trust every transform | Bounded generated-code trace checks | Simulator is not independent if it shares encoder semantics |
| Counterexample reduction | Delta debugging (1999 onward) | Preserve smallest reproducible failure | Minimize C, assembly and instruction traces | Never minimize away the failure oracle |

## Required evidence contract (minimal)

Each qualification case records: `case_id`, `source_sha256`, `tool_revision`,
`target_assumptions`, `oracle_id`, `oracle_ancestry`, `seed` (if applicable),
`expected_observable`, `actual_observable`, `verdict`, `artifact_sha256`,
and `limitations`. Optional fields are absent, not fabricated.

## Independent-oracle rule

Two green tests that share an opcode table, decoder, emulator, or expected-value
generator count as **one oracle family**, not independent corroboration.
Maintain an explicit ancestry edge for every oracle. Recovered GNUPro/QTASM
outputs are historical reference evidence, not automatically authoritative
semantics. An unknown ISA behavior is marked `unknown`, never silently guessed.

## Minimum-change adoption experiment

1. **Discover:** pin existing compiler, assembler, simulator, tests, PR #39,
   and exact CI evidence. Report actual feature and instruction coverage.
2. **Plan:** select three supported defined-behavior C programs and two
   semantics-preserving transformations. Pin widths, signedness, ABI and seed.
3. **Apply:** execute original and transformed programs through the existing
   C -> CY16 assembly -> assembler -> simulator path on free-tier public CI;
   compare only architecturally observable results. Add one independent host
   oracle only where target semantics are explicitly normalized.
4. **Verify:** run positive controls and intentionally broken negative controls,
   preserve exact logs and minimized counterexamples, and distinguish
   shared-ancestry from independent results.

Success: existing CI stays green; negative controls fail as expected; every
claim links to immutable evidence. Failure: stop, preserve counterexample,
do not expand toolchain scope. Revert by removing only this candidate harness.

## Exclusions and gates

No compiler rewrite, new simulator replacement, LLVM/GCC migration, or large
fuzzing framework until an evidence-backed comparison demonstrates benefit.
No proprietary historical executable execution without approved isolation.
No private artifact in public CI. No hardware actuation before S04 HPI RAM
gate. Keep PRs draft and maintain parent chain.
