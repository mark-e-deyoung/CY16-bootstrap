# DE2-115 automated CY16 recovery laboratory — deployment proposal

Status: proposed architecture; no physical deployment or HPI qualification claimed.

## Reuse prior work before new hardware

Prior DE2-115 work identifies LiteX/VexRiscv, a CY7C67200
Wishbone HPI bridge (historically at 0x82000000), Terasic/Nios
reference initialization, SignalTap/LiteScope capture, a
Qsys-to-LiteX intermediate representation, and Quartus 25.1
build containers. Reconcile live branches and actual board
bitstreams before reusing these assumptions. Prior five-board
farm design already called for board IDs, USB port inventory,
board locks, and a single deployment controller.

## Minimum hardware topology

Agent Dispatch scheduler -> always-on Linux lab worker
-> USB-Blaster/JTAG + UART or qualified Ethernet management
-> DE2-115 FPGA -> on-board CY7C67200 HPI bus.

The FPGA implements a bounded sequencer, HPI timeout and
turnaround checks, address allowlists, readback and timestamped
raw trace. Host handles durable experiment artifacts and
differential comparison. Start with one physically inventoried
board; only scale after reproducible cable/board identity.

Optional later: remotely controlled power, independent logic
analyzer, additional DE2-115s, dedicated watchdog/controller.
Power control must be fail-safe and must not energize unknown
I/O wiring.

## Software boundaries

1. **Build workcell:** reproducible Quartus/LiteX build, signed or
   hashed .sof, timing reports, pin constraints, firmware images.
   No direct board access for arbitrary build agents.
2. **Lab controller:** exclusive board lease, identity verification,
   approved image selection, serial/JTAG connection discovery,
   guarded programming, experiment runner, reset and recovery.
3. **FPGA instrument:** versioned register API for read-only HPI,
   later bounded RAM write/restore and code execution; bounded
   queues, watchdog, trace buffer, explicit bus errors.
4. **Evidence service:** immutable manifest, raw HPI capture,
   FPGA build ID, chip/BIOS ID, binary SHA, simulator trace,
   C semantic oracle, verdict and minimized reproducer.
5. **Planner:** selects probes by information gain, risk and
   compiler unblock; proposes changes through DLE, never
   automatically promotes unsupported behavior.

## Human / automation / agent interfaces

Human: concise board readiness, live gate state, run timeline,
failure explanation and replay link.
Automation: deterministic JSON CLI for discover/observe, plan,
apply and verify; idempotency key and exit status.
Agents: same structured API with bounded permissions; no
arbitrary JTAG, shell, raw MMIO or power switching.

## Safe staged deployment

L0: inventory board, physical connection, power, USB/JTAG IDs,
pin constraints and voltage; no output drive.
L1: golden FPGA diagnostic image, read-only JTAG/serial capture.
L2: HPI bus read-only qualification, compare Terasic/Nios timing
and Linux c67x00 host-interface evidence; diagnose all-zero
readback and turnaround/reset before writes.
L3: S04 approved bounded RAM write/read/restore with address
guards and independently verified rollback.
L4: hand-encoded CY16 probe with independent expected bytes,
bounded execution and external mailbox readback.
L5: simulator differential tests, compiler-generated probes,
automatic minimization and regression promotion.
L6: board farm scheduling after independent per-board calibration.

## Research patterns and adoption

Chipyard/FireSim: FPGA bridge to silicon, independent execution
comparison, reusable run receipts; adopt pattern, not stack.
RISCV-DV: constrained-random and directed generation, coverage
feedback, illegal encoding cases; build a minimal CY16 generator.
DUET: FPGA-accelerated differential verification; preserve
fine-grained trace/provenance as instrument permits.
VTEST / software-defined instruments: unify configuration,
capture, reset and host APIs; avoid commercial dependency.
Multilingual concept sweep (English, Chinese, Japanese,
German, French): no proven turnkey CY16 framework found.
Treat search results as transferable methods, not validation
of compatibility.

Sources:
- https://chipyard.readthedocs.io/en/stable/Advanced-Concepts/Chip-Communication.html
- https://github.com/ucb-bar/chipyard/blob/main/docs/Advanced-Concepts/Debugging-RTL.rst
- https://github.com/chipsalliance/riscv-dv
- https://ieeexplore.ieee.org/document/10617632/
- https://ieeexplore.ieee.org/document/11141583/

## Deployment controls

Private-repo workloads via approved Agent Dispatch executors;
do not consume private GitHub-hosted Actions minutes, including
dispatcher control plane. Public non-sensitive source tests may
use public GitHub Actions. Build and physical programming are
separate; require exclusive board lease and evidence-backed
approval for transitions to write/execute gates.

## Next actionable tasks

A. Reconcile actual DE2-115 repo/branch, bridge RTL, Quartus
pin assignments, latest HPI readback evidence, and board census.
B. Produce a minimal read-only HPI diagnostic image and mock
host protocol; test software against an FPGA simulation first.
C. Prepare an on-host lab worker package with read-only discovery,
board lease, dry-run plan and receipt capture.
D. Run live HPI read-only experiment when a connected board
and approved lab executor are verified; keep S04 closed until
physical safety checks pass.
