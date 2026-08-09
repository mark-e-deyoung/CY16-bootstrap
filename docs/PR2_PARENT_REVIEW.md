# PR #2 parent review findings

Review date: 2026-08-09

Reviewed head: `32da72aa1ec59c6f5f9490df534a125f7f5a247d`

Tracking issue: #10

This review covers the 18-file parent change that adds the source/provenance record, AN048-shaped clean-room fixture, SCAN configuration-write support, and source-derived simulator corrections. It separates parent hardening from the parallel control-flow, manifest, and legacy-recovery children.

## Parent findings and dispositions

### Core SCAN parsing accepted ambiguous trailing data

**Finding:** The parser could ignore a final byte, stop at a zero signature without checking remaining bytes, accept payload on CALL/JUMP, and treat unknown opcodes as ordinary address records without an explicit policy.

**Disposition:** The issue #10 child now:

- accepts exact end-of-input or all-zero terminator/padding;
- rejects a one-byte suffix and non-zero bytes after a terminator;
- requires exact CALL/JUMP and WRITE_CONFIG record shapes;
- rejects unknown opcodes by default;
- permits unknown address-based records only through the explicit `allow_unknown=True` archaeology option and CLI switch.

PR #6's manifest implementation and the DE2-115 consumer must continue to parse independently. Shared project parsing is not a trust substitute.

### Builders silently truncated deployment fields

**Finding:** Generic `word_to_le()` masking allowed record addresses, length, and wrapping metadata to be silently reduced to 16 bits.

**Disposition:** SCAN builders now validate opcode, address, body length, payload type, base, setup address, and call address before encoding. CALL/JUMP payloads and use of the generic builder for WRITE_CONFIG are rejected.

The generic format layer does not add DE2-115 HPI alignment/range policy; that remains a consumer/loader responsibility.

### Simulator image loading could extend memory past 64 KiB

**Finding:** Python slice assignment could grow the simulator bytearray if an image crossed `0xFFFF`.

**Disposition:** The established simulator implementation is preserved in `sim_core.py`. The public `sim.py` wrapper provides a bounded `CPU.load()` and `run()` while retaining the existing instruction behavior and CLI. It rejects invalid bases and images that exceed the 64 KiB machine model and asserts that load cannot resize memory.

Instruction and data accesses retain the existing 16-bit wrap behavior.

### AN048 fixture did not assert clean simulator completion

**Finding:** `run()` records execution errors in trace output. The integration fixture checked final state but not the absence of `ERROR:` trace entries.

**Disposition:** The AN048 acceptance test now requires an error-free trace before accepting the MMIO and SCAN results.

The general simulator retains trace-tolerant behavior for debugging; a future strict-execution API can be considered separately.

### Source revision placeholders looked authoritative

**Finding:** `Rev. *B` and `Rev. **` could be mistaken for verified metadata.

**Disposition:** The source index now states that the exact AN048 and AN6010 revision/date metadata has not yet been established from the retained copies. It records revisions only when verified.

## Parallel-child boundaries

This review child does not implement or duplicate:

- PR #4 — relative branches, INT, historical macros, and control-flow conformance;
- PR #6 — versioned artifact manifests, deterministic producer validation, and cross-repository contract;
- PR #9 — local disk/archive fingerprint scanner and recovery workflow.

Shared CLI registration and `pyproject.toml` conflict handling remain governed by integration issue #8.

## Provenance and licensing review

The AN048-shaped fixture is clearly project-owned and behavioral; no vendor application source is copied. Linux and Stierlitz are recorded as GPL behavioral references, and UIUC/Terasic-derived material remains provenance-sensitive.

The retained vendor PDFs and supplied `scanwrap.c` reference remain subject to their own terms. This review does not declare them redistributable and is not legal clearance for existing repository artifacts.

## Validation and merge readiness

The validation workflow now runs on stacked pull requests instead of only PRs targeting `main`.

PR #2 remains draft until:

1. this child is incorporated;
2. the full compiler build and pytest ladder pass at the resulting head;
3. setup-stub and AN048 integration anchors remain green;
4. the reduced parent diff and provenance boundary are rechecked.
