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
