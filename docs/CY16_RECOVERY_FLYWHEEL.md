# CY16 silicon/compiler/emulator recovery flywheel

**Mission:** iteratively recover enough independently witnessed CY16
behavior to compile C programs that execute correctly on real Cypress
hardware. This is an experimental recovery process, not a one-shot
conformance test.

## Closed loop

Observe/document hypothesis -> select a discriminating experiment ->
generate byte-anchored probe -> execute via qualified DE2-115 HPI ->
capture raw observations -> compare hardware, emulator and expected C
semantics -> minimize discrepancies -> revise specification/model/
compiler -> replay every previous witness -> promote qualified
capabilities -> choose the next experiment.

## Bootstrap tiers

- Tier 0: FPGA/HPI read-only witness, physical interface and BIOS
  identity. No code execution.
- Tier 1: independently sourced instruction bytes and RAM mailbox
  write/read after S04 gate; no compiler dependency.
- Tier 2: assembler-generated probes, byte-checked against independent
  encoding vectors; simulator is an additional prediction, not oracle.
- Tier 3: compiler-generated minimal C probes only for already
  qualified ABI and instruction subset.
- Tier 4: differential programs, interrupts, bank switching, BIOS
  interaction, device profiles and optimized compiler output.
- Tier 5: application workloads with repeatable hardware passes.

## Probe record schema v0

`id, hypothesis, source_refs, applicability, confidence,
required_tier, initial_state, binary_sha256, generator_sha,
board_bitstream_sha, chip_revision, bios_revision,
allowed_addresses, forbidden_effects, max_runtime,
expected_observations, raw_hpi_trace, snapshot_provenance,
emulator_trace, compiler_artifacts, verdict, discrepancy_class,
minimized_reproducer, promotion_decision`.

Verdicts: PASS, FAIL, INCONCLUSIVE, INFRA_BLOCKED.
A probe's 'PASS' never proves a wider ISA feature than its
explicit claim. Never erase failed observations after fixes.

## Discrepancy triage

1. Verify HPI read/write stability, address guards, timeout and
   snapshot mechanism before attributing silicon behavior.
2. Compare source-derived machine words with assembled bytes.
3. Replay identical bytes in emulator and hardware with the
   same explicitly captured initial state.
4. Use an independent reference C semantics evaluator only where
   the C behavior is defined and ABI is established.
5. Delta-debug the shortest diverging instruction sequence and
   vary one dimension at a time: flags, operands, bank, memory,
   interrupt, timing or BIOS context.
6. Convert each discrepancy into a regression witness before
   changing either emulator or compiler.
7. Promote only after repeated silicon observations and independent
   reproduction. Preserve contradictory evidence as unresolved.

## Experiment selection

Prioritize probes by
`expected uncertainty reduction * downstream compiler unblock
/ (execution cost + risk + setup time)`.
Start with flags, operand addressing, bank/stack, CALL/RET,
branches and memory aliases. Defer dangerous DMA and unknown
MMIO. Prefer paired probes that distinguish competing hypotheses
rather than high-volume random instructions.

## Execution control

Public non-sensitive CI may run on public repository Actions.
All private fixtures and private-repo workloads use approved
Agent Dispatch runtimes, without private GitHub-hosted minutes.
The HPI instrument requires an approved local physical executor;
remote dispatch must not imply that the chip is currently
connected. Preserve discover/observe -> plan -> apply -> verify,
reproducible/repeatable/reversible/idempotent runs, bounded
permissions and independent safety interlocks.

## Hard gates

No active hardware probing before voltage/pin/bus ownership
verification, stable HPI read-only qualification and S04
RAM-safety approval. No compiler-generated probe before
hand-coded byte and loader witnesses. No claim of full compiler
or emulator qualification from mutual agreement alone.

## MVP success criterion

At least one independently byte-anchored CY16 program is
loaded and executed on physical hardware; a DE2-115-captured
memory result matches the emulator and an independent expected
result on repeated runs, with raw traces, hashes and recovery
procedure preserved. This is **flywheel MVP**, not full
compiler/emulator qualification.
