# CY16 specification reconciliation — evidence-to-implementation ledger

Status: **initial reconciliation, not specification conformance**.
Authority: existing `docs/CITED_FINDINGS.md` [S1–S6], `docs/POAM.md`, and draft PR #39.
Do not reproduce proprietary specification tables here. Citations below refer to
existing project source keys; original page/section verification is **pending**.

## Evidence classes

- **Documented:** existing project summary attributes a statement to a historical source; requires page-level recheck.
- **Implemented:** behavior exists in project code; this does not independently validate it.
- **Golden:** exact independently sourced bytes observed.
- **Provisional:** project design choice, not necessarily vendor compatible.
- **Unknown:** no sufficient evidence yet. Never fill unknowns with inference.

| Contract | Historical evidence | Existing implementation | Reconciliation / gap |
|---|---|---|---|
| 16-bit instruction with opcode and two operand-mode fields | S2, summarized in CITED_FINDINGS §4 | `src/cy16boot/isa.py`: `encode_alu` (4+6+6) | Implemented; exhaustive legality and page-level reference unverified |
| R0–R15 and two register banks | S2, §3 | `src/cy16boot/sim.py`: `regs[16]` | **Gap:** simulator models one bank; bank switching and interrupts not qualified |
| R8–R14 pointer registers; R15 stack special | S2, §§3–5 | `asm.py` indirect modes; `sim.py` pre-decrement/post-increment | Partial; illegal byte forms and precise stack semantics require negative tests |
| Byte-addressable unified memory, aligned word accesses | S2, §§3–4 | `sim.py`: 65536-byte array, little-endian `readw/writew` | **Gap:** current word access wraps; no alignment exception/rejection shown |
| ALU and condition flags | S2, source section not yet pinned | `isa.py` opcode/condition constants; `sim.py` Z/C/S/O | Partial; each flag and exceptional case needs independent oracle |
| Hardware/software interrupts | S2, §6 | ABI v0 deliberately excludes interrupt handlers | Not qualified; avoid treating CALL-like software interrupt as full hardware ISR |
| BIOS memory map, reset, ROM and vectors | S5, §7 | `sim.py` flat memory; startup profiles in `libcy16/` | **Gap:** simulator flat map does not model ROM/MMIO/vectors/reset faithfully |
| BIOS software-vector compatibility | S5, §8 | Runtime design intent | No cross-BIOS version compatibility proof |
| CY16 C calling convention | S1/S4 partial context | `docs/ABI_V0.md` R0–R3 args, R0 return, R15 stack | **Provisional:** explicitly not established GNUPro ABI compatibility |
| GNUPro ELF and relocations | S1/S3, §§1–2 | `asm.py` emits flat binary | **Gap:** GNUPro ELF machine/relocation coverage not demonstrated |
| SCAN image record handling | S3/S6, §§10–12 | `docs/SCAN_FORMAT.md`, `cy16boot.scan` | Golden setup stub words; full COPY/JUMP/CALL semantics require separate proof |
| BIOS-cooperative startup/Idle_Task | S3/S4, §§9,11 | `libcy16` startup profiles | Need separate BIOS-cooperative vs standalone executable contracts |

## Conflicts and ambiguities to resolve first

1. **Register banks:** specification summary says two banks; software model stores one.
   Establish bank select mechanism, visibility, reset bank, and interrupt interaction.
2. **Word alignment:** specification summary requires even alignment; simulator's
   `readw/writew` currently accept odd addresses. Determine actual hardware behavior
   before choosing trap, masking, or undefined behavior.
3. **Memory map:** simulator's writable 64 KiB array is not a CY7C67200/CY7C67300
   hardware model. Define BIOS, standalone and test profiles separately.
4. **ABI provenance:** project ABI v0 must never be labeled GNUPro-compatible
   without recovered ABI evidence and cross-toolchain tests.
5. **SCAN command semantics:** independently verify command records and load
   effects; avoid conflating correct parsing with safe hardware execution.

## Minimal next evidence batch

For each conflict, extract **source ID, document version, page/section, exact
technical claim in original words (private only), normalized public-safe
assertion, applicability (67200/67300, BIOS version), confidence, and unresolved
questions**. Keep original copyrighted text in private evidence storage.

Then add deterministic tests **before** modifying the simulator. Negative tests
must distinguish accepted behavior from unmodeled behavior. Do not implement
guessed semantics. Pin original artifact hashes and source ancestry.

## Decision gates

- Source conflicts: unresolved until source precedence and applicability proven.
- Simulator changes: separate reversible PR with failing-before/fixed-after tests.
- Compiler/ABI changes: only after instruction and ABI contract reconciliation.
- Physical tests: S04 HPI RAM gate remains closed.
- Historical executables: no execution without approved isolated runtime.


## Original-document reconciliation batch 1 — 2026-10-13

Source copies located in private Library: `infineon-cy16-programmers-guide-usermanual-en.pdf`
(Programmers Guide v1.1, rev 1.1 dated 2003-07-02) and
`OTG-Host BIOS User Manual2.pdf` (BIOS User's Manual v1.1).
These are **page-anchored normalized findings**, not reproduced proprietary tables.

### REGBANK — resolved mechanism, implementation gap remains

Programmer's Guide §1.2, §1.3.3, printed pp. 1-1, 1-3 to 1-4:
REGBANK is a 16-bit memory-mapped R/W register at **0xC002**.
R0–R15 are RAM-mapped as 16-bit words at
`(REGBANK & 0xFFE0) | (register_number << 1)`.
REGBANK bits 0–4 are ignored. Example: REGBANK 0x0100 makes R14
address **0x011C**. The guide describes two banks as an architectural
usage pattern, but the base-register mechanism permits RAM-selected
register windows; do **not** hardcode a two-element bank selector
without further evidence. Current `sim.py` has `regs[16]` detached
from memory and no REGBANK mapping. **Confirmed modeling gap.**

### FLAGS — architectural location and width distinction

Programmer's Guide §1.3.4, printed p. 1-4:
FLAGS is R/W at **0xC000**, with Z, C, O, S and global interrupt-enable I.
The guide states that flags are set for **16-bit operations only**.
Current simulator models Z/C/O/S as booleans; it does not model FLAGS
as mapped MMIO or I. Flag-update behavior of individual instructions
still requires §2/§3 reconciliation. **Confirmed modeling gap.**

### Word alignment — specification established, response still open

Programmer's Guide §1.2, printed p. 1-1: byte moves and **even-aligned**
word moves. §1.3.16, printed p. 1-8: byte-wide indirect R15 forbidden;
R15 indirect write pre-decrements, read post-increments. The guide's
statement establishes a legality constraint but does **not** establish
what silicon does for an illegal odd-address word access. Current
`sim.py` permits such accesses. Mark **unsupported/unqualified**,
not a confirmed hardware trap or masking behavior.

### Memory and reset — BIOS profile, not universal RAM

BIOS User's Manual v1.1, Fig. 1-2, printed p. 1-6:
0x0000–0x00FF interrupt vectors; 0x0100–0x011F primary registers;
0x0120–0x013F swap registers; 0x0140–0x0148 HPI interrupt/mailbox;
0x04A4–0x3FFF user-code internal RAM; 0xC000–0xC0FF control registers;
0xE000–0xFFFF internal BIOS ROM. Intermediate BIOS-reserved ranges
and external-memory regions require per-device profiles.
Programmer's Guide §1.3.6, printed p. 1-5: hardware reset PC **0xFFF0**.
The current simulator's 64 KiB writable flat array is a deliberate
test abstraction, **not** the BIOS profile. Avoid blindly making all
these addresses writable or executable in a hardware-faithful mode.

### Source authority and next gate

Primary document statements above supersede earlier unanchored
summaries for the specified pages. Before coding, inspect source
images for the memory-map figure and register formula, capture
source hashes and applicability by chip/BIOS version, and write
negative tests for bank mapping, FLAGS MMIO, and odd-word accesses.
No new silicon behavior is inferred from simulator implementation.
