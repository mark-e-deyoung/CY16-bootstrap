# External implementation notes

These projects and source trees are useful as behavioral references, but they do not all share the same architecture, target chip, board, or license. Reuse must be deliberate.

## Linux `c67x00`

Snapshot used during this research:

```text
torvalds/linux@bf4afc53b77aeaa48b5409da5c8da6bb4eff7f43
```

Relevant directory:

```text
drivers/usb/c67x00/
```

### Useful behavior

- HPI logical register map and 125 ns minimum cycle spacing.
- ADDRESS-then-DATA block transfers and little-endian payload handling.
- LCP serialization, mailbox completion, `COMM_RESET`, and `COMM_EXEC_INT`.
- SIE initialization, port reset, interrupt clearing, and TD submission.
- Host scheduling and bandwidth calculations derived from the BIOS manual.
- Current driver comments state that it was derived from the Cypress CY7C67200/300 Linux driver.

### Project use

- Use as a protocol oracle for tests and state sequences.
- Independently derive constants from public Cypress documents where possible.
- Do not copy GPL source into MIT components without choosing and documenting a compatible license boundary.
- The maintained Linux HCD is not a drop-in Zephyr stack and should not dictate the CY16 compiler ABI.

## UIUC DE2-115 project

Pinned source:

```text
markubiak/sv-parametric-equalizer@8e7a30fae34027629a318205da072e7ce01cf57c
```

Relevant paths:

```text
hpi_io_intf.sv
software/usb_kb/
software/usb_kb/cy7c67200.h
nios_system.qsys
nios_system.sopcinfo
Final_Project.qsf
```

### Useful behavior

- Same Terasic DE2-115 board and Cypress device.
- Board-specific signal names, polarities, and Quartus/Qsys mapping.
- Nios HPI access functions and BIOS-reset sequence.
- Transfer-descriptor and keyboard-enumeration examples.
- Generated system metadata may explain implicit bus latency that allowed the simple HPI wrapper to operate.

### Project use

- Compare exact pin constraints with `SemperSupra/DE2-115`.
- Generate representative Nios transaction traces and compare them with the LiteX bridge.
- Use its TD structures as candidates, then verify each field against the BIOS manual.
- Treat the large Cypress/Terasic-derived header and examples as provenance-sensitive; their repository presence does not establish a permissive license.

## Stierlitz

Pinned source:

```text
asciilifeform/Stierlitz@783524ebb77b825a2ad6368bf7b3e60f23f7d738
```

### Useful behavior

- Explicit multi-state HPI read/write sequencing.
- Data-bus output-enable transitions.
- Late read sampling and write completion at strobe deassertion.
- IRQ-triggered mailbox access and turnaround to idle.

### Limitations

- CY7C67300 on Xilinx ML501, not CY7C67200 on DE2-115.
- Custom mailbox application rather than the standard Cypress BIOS host stack.
- No replacement for AN6010, the BIOS manual, or the CY16 GNUPro tools.
- GPLv3-or-later.

Use it for RTL sequencing comparisons and testbench ideas, not as the application architecture.

## Historical Cypress Linux tree

Expected installed path:

```text
C:\Cypress\USB\OTG-Host\Source\coprocessor\linux\drivers\usb\cy7c67300
```

Named files/functions from official Infineon KBAs:

```text
cy7c67200_300_hcd.c
cy7c67200_300_hcd_simple.c
cy7c67200_300_lcd.c   # published spelling; possibly lcp/init typo
hcd_irq_resumeX
DEFAULT_EOT
MAX_FRAME_BW
usbd\dedev\de1_bios.asm
```

The upstream Linux driver is a rewrite/derivative and does not necessarily preserve all original filenames, LCP helpers, or application examples. Recovering this tree would provide valuable comparison material.

## CY4640 SCAN-to-LCP loader

An Infineon KBA identifies CY4640 version 1.1 and later as a reference for loading a standalone image over the co-processor interface.

The documented approach is:

1. parse SCAN signatures and opcodes;
2. translate COPY operations into direct HPI RAM writes;
3. translate configuration-space writes into `COMM_WRITE_CTRL_REG`;
4. translate CALL/JUMP into corresponding LCP operations;
5. continue until the image is loaded and execution begins.

The KBA provides a concrete configuration-write record:

```text
B6 C3 03 00 09 3A 22 22
```

Interpreted as:

- signature `0xC3B6` in little-endian byte order;
- length 3 after the opcode;
- opcode `0x09`, Write Configuration;
- configuration offset `0x3A`, implying control address `0xC03A`;
- value `0x2222`.

### Project implication

The current SCAN parser recognizes COPY, JUMP, and CALL. Before claiming general Cypress compatibility, add the documented configuration-write opcode and route it through a verified LCP control-register helper in the DE2-115 loader. Do not perform it as a direct HPI write to `0xC03A`.

## Xilinx ML40x reference design

Historical target:

```text
ml40x_usb.zip
```

A surviving mirror of AMD/Xilinx Answer Record 31312 associates it with Cypress `SD1025` and ML401/ML403 support. Expected value includes an FPGA HPI peripheral, embedded-CPU driver, and possibly firmware/EEPROM images.

Until recovered, this remains an artifact lead rather than an implementation source.

## Architectural separation

Keep three layers distinct:

1. **CY16 toolchain** — ISA, ABI, compiler, assembler, simulator, SCAN packaging.
2. **External HPI loader** — FPGA bus timing, direct-memory access, LCP, SCAN translation.
3. **USB host stack** — SIE initialization, TD scheduling, enumeration, class behavior.

A source may be strong in one layer and misleading in another. For example:

- the Programmer's Guide is normative for CY16 instruction encoding but says little about FPGA HPI timing;
- Stierlitz is useful for HPI state sequencing but not for BIOS USB-host behavior;
- Linux is useful for HPI/LCP/HCD behavior but not for the original CY16 GNU ABI;
- AN048 is useful for toolchain integration but not for proving the DE2-115 electrical path.
