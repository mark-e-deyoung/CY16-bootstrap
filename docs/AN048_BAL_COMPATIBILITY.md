# AN048 BAL compatibility target

AN048 documents a small EZ-Host/EZ-OTG application from source through EEPROM deployment. It is valuable because it exercises the entire historical toolchain rather than only isolated instruction encodings.

## Historical flow documented by AN048

```text
StartupNoBIOS.s or StartupWithBIOS.s
BAL.c
    -> cy16-elf-as / cy16-elf-gcc
    -> cy16-elf-ld using BAL.ld
    -> ELF image
    -> cy16-elf-objdump listing
    -> cy16-elf-objcopy -O binary
    -> scanwrap raw.bin scan.bin 0x00001000
    -> qtui2c scan.bin -f
```

The linker script places `_start` and the program at `0x1000`. AN048 explicitly requires the `scanwrap` base to match the link/start address because wrapping does not relocate the binary.

## Why the fixture is clean-room

The application note includes Cypress source under a restrictive source-code notice. The project therefore uses original fixtures that reproduce the relevant characteristics without copying that source:

- a freestanding 16-bit C type;
- volatile memory-mapped I/O;
- a named application entry point;
- placement at `0x1000`;
- raw-binary generation;
- SCAN COPY and CALL records;
- simulator-observable behavior.

See `fixtures/an048-bal`.

## Current executable acceptance test

`tests/test_an048_fixture.py` performs:

1. read the project-owned `BAL.c` fixture;
2. compile it with the CY16 backend;
3. assemble it into a flat binary based at `0x1000`;
4. execute `_bal_fixture` in the simulator;
5. require the expected volatile write/read result at `0xC03A`;
6. SCAN-wrap the binary with the same base;
7. decode the image and verify the payload COPY and final CALL address.

This is the first project test that deliberately spans C, assembly, binary, simulation, and deployment packaging in the shape of a historical Cypress example.

## Startup profiles

### No-BIOS takeover

AN048's minimal no-BIOS startup transfers control to `main` after the ROM BIOS has performed reset-time initialization and loading. The project fixture currently models the transfer to the application entry point.

A production no-BIOS runtime must also document:

- stack ownership;
- `.bss` clearing policy;
- return-from-main behavior;
- which BIOS services cease to be available;
- interrupt-vector ownership.

### BIOS-cooperative operation

AN048 describes preserving BIOS background services by replacing an IDLER vector and invoking the BIOS idle chain periodically from Timer0. This supports the legacy UART/USB loading and inspection utilities.

The project retains `StartupWithBIOS.s` as a staged compatibility target. It is not yet considered hardware-ready because the following require dedicated conformance tests:

- vector-address calculation;
- Timer0 hardware ISR installation;
- flags/register preservation;
- BIOS software interrupts for PUSHALL, IDLE, and POPALL;
- Timer0 reload;
- delayed effect of `STI`;
- return semantics.

## Remaining historical-tool compatibility

| Capability | Current state | Next evidence |
|---|---|---|
| C to CY16 assembly | Active compiler baseline | fixture test in CI |
| CY16 assembly to flat binary | Active assembler baseline | fixture test in CI |
| Disassembly/listing | Project listing/disassembler exists | compare with recovered GNUPro listing |
| Multiple-object linking | Not a full GNU linker replacement | relocatable format/linker track |
| ELF/BFD compatibility | Future convergence | recover original binutils patches or infer ABI from objects |
| SCAN wrapping | Active project implementation | golden legacy-image comparisons |
| EEPROM programming | Not implemented in this repo | separate host utility/hardware adapter decision |
| GDB/Insight/SID | Future archaeology | recover CY16 GNUPro binaries/source and protocol details |

## Hardware handoff

The generated SCAN image must not be used to diagnose USB behavior until the companion DE2-115 project passes:

1. valid direct internal-RAM write/read;
2. `COMM_RESET`/`COMM_ACK` BIOS handshake;
3. SCAN COPY with byte-for-byte readback;
4. verified LCP CALL/JUMP behavior.

`0xC03A` is valid for code executing on the internal CY16 CPU. It is not evidence that an external HPI master may directly access all processor-control registers.
