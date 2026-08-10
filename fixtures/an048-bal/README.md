# AN048 BAL compatibility fixture

This directory converts the useful parts of Cypress AN048 into a clean-room, executable acceptance target without copying the application note's source code.

## Historical workflow represented

AN048 documents this sequence:

```text
C and assembly
  -> cy16-elf-as / cy16-elf-gcc
  -> cy16-elf-ld at 0x1000
  -> cy16-elf-objdump listing
  -> cy16-elf-objcopy raw binary
  -> scanwrap at the same 0x1000 base
  -> qtui2c EEPROM programming
```

The bootstrap project's equivalent validation path is:

```text
BAL.c
  -> cy16cc.codegen.compile_c
  -> CY16 assembly
  -> cy16boot.asm.assemble at 0x1000
  -> cy16boot.sim.run
  -> cy16boot.scan.wrap_payload
  -> cy16boot.scan.parse_scan
```

## Files

- `BAL.c` — original project-owned volatile-MMIO fixture, not Cypress source.
- `StartupNoBIOS.s` — minimal transfer-to-application compatibility target.
- `StartupWithBIOS.s` — staged BIOS-cooperative target; retained but not yet in the green build.

## Current green acceptance

`tests/test_an048_fixture.py` verifies:

1. the C fixture compiles to CY16 assembly;
2. the assembly produces a binary based at `0x1000`;
3. the simulator executes the volatile write/read correctly;
4. SCAN packaging uses the same base and calls the compiled entry point;
5. SCAN decoding returns the expected COPY and CALL records.

## Remaining convergence work

- Relocatable objects and a linker capable of combining startup and compiler output.
- Full GNUPro-compatible symbol and section handling.
- BIOS-cooperative Timer0/IDLER startup with tested `INT`, flag preservation, and ISR return behavior.
- Historical listing/map comparison if a known-good CY16 GNUPro output is recovered.
- Hardware deployment after DE2-115 HPI RAM readback and LCP handshake pass.

## Legal boundary

The fixture is a behavioral reimplementation. Do not replace it with the AN048 source text unless the applicable Cypress license and repository distribution policy have been reviewed.
