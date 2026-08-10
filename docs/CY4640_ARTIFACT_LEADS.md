# CY4640 alternate artifact-recovery leads

The CY4640 Mass Storage Reference Design Kit is a second possible route to the same CY16 tools, BIOS documents, SCAN utilities, and co-processor loader behavior sought from the missing CY3663 distribution. Official Infineon knowledge-base articles describe CY4640 version 1.1 and later as including the development tools needed to rebuild its firmware and as providing a reference implementation for downloading standalone firmware over HPI.

## Why CY4640 matters

The CY4640 is narrower than CY3663—it focuses on the EZ-Host mass-storage design—but surviving support articles indicate that it contains:

- the CY16 development tools;
- BIOS/SCAN documentation;
- standalone mass-storage firmware;
- HPI/co-processor download support in version 1.1 and later;
- hardware schematics, Gerbers, and OrCAD sources;
- a SCAN parser that translates configuration writes into LCP operations.

A complete CY4640 1.1 installation may therefore recover several high-priority pieces even if a CY3663 ISO is never found.

## Confirmed historical paths and files

### Firmware and SCAN build

```text
C:\Cypress\USB\OTG-Host\Source\stand-alone\msc
```

The documented command to produce `msc_scan.bin` is:

```text
make wrap
```

The related getting-started documentation is described as:

```text
C:\Cypress\USB\OTG-Host\Docs\CY4640\CY4640 1_1 GettingStarted.pdf
```

### BIOS/SCAN documentation

The standalone-over-coprocessor article points to BIOS User Manual section 1.7.2 in the installed Docs directory for scan signatures and scan codes.

### Hardware package

An Infineon KBA gives the default hardware directory as:

```text
C:\Cypress\USB\OTG-Host\Hardware\CY4640
```

The published article contains `OGT-Host` in one path spelling, which is likely a typographical error for `OTG-Host`. Search both spellings when examining disk images or indexed archives.

Expected contents include:

- shipped-board schematics;
- Gerber files;
- a simplified design with nonessential development-board components removed;
- OrCAD `.dsn` files;
- CPLD/bootstrap configuration design material.

### Debugging documentation

A separate KBA identifies:

```text
$HOME/Docs/CY4640/CY4640 Debugging Options
```

This may contain useful information about reduced debug builds, serial diagnostics, and hardware tracing.

## Confirmed SCAN-to-LCP behavior

CY4640 1.1+ is explicitly identified as the reference implementation for parsing a scanwrapped firmware image over the co-processor interface. The documented configuration-write example is:

```text
B6 C3 03 00 09 3A 22 22
```

Interpretation:

- signature `0xC3B6` in little-endian byte order;
- record length `3` after the opcode;
- opcode `0x09`, Write Configuration;
- control-space offset `0x3A`, implying address `0xC03A`;
- value `0x2222`.

The external loader translates the record to `COMM_WRITE_CTRL_REG`; it does not directly write `0xC03A` through HPI.

This behavior is now represented by project-owned decoding and tests, but the LCP command's parameter/result layout still needs a verified source before hardware execution is enabled.

## New acquisition targets

Search for these exact names and directory fragments:

```text
CY4640 1_1
CY4640_1_1
CY4640 RDK
CY4640 GettingStarted.pdf
CY4640 Debugging Options
msc_scan.bin
Source\stand-alone\msc
Hardware\CY4640
scanwrp2
make wrap
```

Also search old development PCs and media for either root:

```text
C:\Cypress\USB\OTG-Host
$HOME/Docs/CY4640
```

## Expected value ranking

1. **CY4640 1.1 installer/archive** — may include the full relevant toolchain subset and loader source.
2. **Installed `Source` and `Docs` directories** — enough to recover the SCAN parser, mass-storage example, and manuals.
3. **`msc_scan.bin` plus matching source/listing/map** — strong golden corpus for SCAN decoding and compiler comparison.
4. **Hardware directory** — useful for bootstrap, HPI, CPLD, EEPROM, and bus-contention comparison.
5. **Debugging Options document** — useful for historical GDB/serial/tracing workflow reconstruction.

## Search result as of 2026-08-09

Follow-up exact-name searches recovered official Infineon descriptions and paths but did not surface a downloadable CY4640 1.1 installer, source archive, or `msc_scan.bin`. The material remains a high-value preservation target rather than an available dependency.

## Intake rule

Treat a recovered CY4640 package like the CY3663 material:

1. preserve the original archive and hash it;
2. inventory licenses before redistribution;
3. keep vendor source/binaries outside the permissively licensed code tree unless rights are clear;
4. derive original tests, format descriptions, and compatibility fixtures;
5. compare CY4640 and CY3663 duplicate files by hash to identify common toolchain/framework releases.
