# DE2-115 CY16 silicon-oracle experiment protocol

Purpose: use a real CY7C67200/CY7C67300 (identified by board
inventory, not assumed) to independently qualify compiler output
and emulator execution. This is a **proposed gated protocol**, not
evidence of an operational hardware link.

## Measurement architecture

Host controller -> DE2-115 FPGA (LiteX/VexRiscv or dedicated
bounded sequencer) -> level/voltage-verified HPI wiring ->
Cypress chip. FPGA logs bus transaction requests, ACK/ready,
readback, timeouts and monotonic sequence numbers. Keep host-side
raw log and machine-readable verdict; preserve bitstream SHA,
firmware SHA, board revision, pin constraints and chip/BIOS ID.

The HPI bus is an **external observation channel**, not a full
register trace. Direct visibility of live CPU R0-R15, PC and
FLAGS is **not assumed**. Register/flag observation may require
a short source-vetted monitor routine to snapshot state into
a reserved RAM mailbox, then HPI readback. That routine must
have independent byte-level qualification; its side effects
must be documented. A program's own 'pass' bit is insufficient.

## Safe progressive gates

H0: inventory physical chip, board connections, voltage levels,
clock/reset, FPGA pin map and bus ownership. No drive yet.
H1: passive capture/logic analyzer, verify idle levels and
timing; compare against host-interface datasheet.
H2: read-only ID/ROM/control register access with timeout,
repeatability and independent expected-value oracle.
H3: reserved RAM bounded write/read/restore, verify no BIOS,
interrupt vector, stack or mailbox collision. Requires the
existing S04 HPI RAM gate approval.
H4: ROM BIOS loader/SCAN command qualification with independent
host capture, range guards, and reset/recovery path.
H5: single-instruction probes: isolated scratch RAM, bounded
execution and result snapshot, including negative controls.
H6: compiler fixtures: compile -> assemble -> hash -> load ->
execute -> snapshot -> compare with emulator and C-level oracle.
H7: stress and differential campaigns across chip/BIOS
revisions, repeat boots, edge cases and metamorphic programs.

Stop on stuck bus, mismatched identity, timeout, out-of-range
address, failed restore or unstable readback. Never automatically
retry writes on ambiguous completion without an idempotency
token and readback.

## Independent oracle design

Each experiment has:
- instruction bytes sourced from original docs or independently
  recovered examples (not merely assembler round-trip);
- specified initial RAM, register bank, flags, stack, PC and
  interrupt assumptions;
- allowed effects and forbidden writes;
- bounded execution / timeout / reset strategy;
- raw FPGA HPI trace plus mailbox snapshot (where qualified);
- simulator trace and compiler output hashes;
- expected/actual comparison with tri-state result:
  PASS, FAIL or INCONCLUSIVE (measurement gap).

Differential triage:
- Hardware differs from emulator, while instruction bytes are
  independent: suspect emulator, device profile or measurement.
- Compiler binary differs from source-derived expected bytes:
  suspect compiler/assembler, not emulator.
- Hardware and emulator agree but violate independently
  calculated C semantics: suspect compiler/ABI or common oracle.
- Hardware readback is unstable: infrastructure failure,
  **not** evidence of an ISA defect.

## Useful DE2-115 capabilities

Use FPGA fabric for a deterministic HPI sequencer, timestamped
transaction recorder, timeout watchdog, triggerable signal
capture and on-chip buffering. SDRAM can buffer larger traces;
Ethernet/UART/JTAG may export them depending on qualified board
firmware and wiring. LEDs/switches provide only coarse diagnostics,
not sufficient qualification evidence.

## Current hard hold

Existing DE2-115 integration documentation states that HPI
readback may return 0x0000 and requires control-register and
RAM readback qualification first. **Do not advance to code
injection or execution until the physical interface and S04
safety gate are independently passed.** FPGA I/O voltage and
bus direction must be checked against actual hardware wiring
before enabling outputs.

No experiment in this protocol has been claimed as executed.
