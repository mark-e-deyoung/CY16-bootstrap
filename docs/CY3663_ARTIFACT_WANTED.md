# CY3663 and related artifact recovery catalog

The original CY3663 CD-ROM image and complete GNUPro development environment have not been recovered. This file records exact targets, the evidence for each target, and search results so future work does not repeatedly rediscover the same dead links.

## Highest-priority targets

| Priority | Target | Expected value | Evidence |
|---:|---|---|---|
| 1 | `CY3663 CD-ROM Image v1.0` original ISO/installer | Complete toolchain, Common sources, frameworks, Linux/WinCE drivers, utilities and examples | Former Cypress download page and multiple Infineon support replies |
| 2 | `Common/ISRS.S` | Full mapping of 48 hardware interrupt vectors | Infineon accepted answer to *CY7C67300 Interrupt Vector* |
| 3 | `Common/cy7C67200_300.h` and case variants | Register definitions, BIOS vectors, descriptor pointers and framework interfaces | Infineon standard-request KBA |
| 4 | `Source/coprocessor/de_app` | DE2/DE-family HPI transfers, TD examples, likely source lineage of surviving firmware | Infineon DE2-115 bulk-write answer |
| 5 | `Source/coprocessor/linux/drivers/usb/cy7c67300` | Original Cypress co-processor Linux driver from which the maintained driver descended | Infineon insert/remove KBA |
| 6 | `usbd/dedev/de1_bios.asm` | SOF interrupt handling and device example behavior | Infineon CY7C67200 HPI keyboard answer |
| 7 | `cy7c67200_300_hcd.c` | HCD, EOT configuration, insert/remove handling | Infineon KBAs |
| 8 | `cy7c67200_300_hcd_simple.c` | `MAX_FRAME_BW` and simpler scheduler behavior | Infineon EOT-throughput KBA |
| 9 | `cy7c67200_300_lcd.c` or likely `*_lcp.c`/initialization spelling variants | Required interrupt-enable and routing initialization | Infineon insert/remove KBA; published filename may contain a typo |
| 10 | CY4640 v1.1+ source | SCAN parser that translates configuration writes to `COMM_WRITE_CTRL_REG` | Infineon standalone-over-coprocessor KBA |
| 11 | `scanwrp2` source/binary | Additional SCAN opcode and packaging behavior | Same KBA and legacy utility references |
| 12 | GNUPro CY16 source patches and binaries | Original GCC/binutils/GDB/SID target implementation and ABI evidence | CY3663/GNUPro documentation |

## Xilinx/AMD targets

| Target | Expected contents | Evidence level |
|---|---|---|
| `ml40x_usb.zip` | ML401/ML403 FPGA HPI interface, MicroBlaze/PowerPC software, firmware/EEPROM image | Historical AMD/Xilinx Answer Record 31312 mirror; archive not recovered |
| Cypress `SD1025` package | CY3663/EZ-Host development-kit distribution page/package | Multiple Infineon replies and AR 31312 mirror |
| ML50x/ML605 Cypress board files | Later board variants of the same support package | AR 31312 title/summary |

## Other useful documents and framework sources

- Frameworks Reference Guide/Manual for CY7C67300/CY7C67200.
- `app.c`, `app_pre_init`, `sie1.c`, and `sie1_install_descriptor` from framework example 1.
- Binary Utilities Reference and any source for `qtui2c`, `qtuload`, `qtsload`, `qtsdump`, `qtuarena`, and related tools.
- `BAL.ld`, startup files, and known-good ELF/object/listing outputs from AN048 examples.
- Any CY16 GNUPro release notes or target patches identifying the target triplet and BFD machine number.

## Search log — 2026-08-09

### Confirmed references

1. Infineon *CY7C67200 (EZ-OTG) HPI Keyboard Example* confirms the exact installed path:

   ```text
   OTG-Host\Source\coprocessor\linux\drivers\usb\cy7c67300\usbd\dedev\de1_bios.asm
   ```

   It also confirms CY7C67200 port mapping: Port 1A is BIOS port 0 and Port 2A is BIOS port 2.

2. Infineon *cy7c67200 bulk write on DE2-115* confirms:

   ```text
   C:\Cypress\USB\OTG-Host\Source\coprocessor\de_app
   ```

3. Infineon *Enabling of USB device Insert/Remove interrupt to HPI* confirms the historical Linux path, `hcd_irq_resumeX`, `cy7C67200_300_hcd.c`, and a file published as `cy7C67200_300_lcd.c`.

4. Infineon *Host throughput using Linux driver may be low due to EOT time slot* confirms:
   - `MAX_FRAME_BW` in `cy7c67200_300_hcd_simple.c`, default approximately 4096 bit times;
   - `DEFAULT_EOT` in `cy7c67200_300_hcd.c`, historical default 4800 bit times.

5. Infineon *Can I download a stand-alone firmware image over the co-processor interface?* confirms CY4640 v1.1+ as a reference implementation and documents SCAN opcode `0x09` for a configuration-space write translated into `COMM_WRITE_CTRL_REG`.

6. Infineon *OTG-Host BIOS handling standard requests* confirms `cy7C67200_300.h` in the Common directory and identifies framework paths/functions for descriptor installation.

7. Infineon *CY7C67300 Interrupt Vector* confirms `ISRS.S` in the Common directory as the vector-map source.

8. A surviving mirror of AMD/Xilinx Answer Record 31312 names:

   ```text
   http://www.cypress.com/design/SD1025
   http://www.xilinx.com/products/boards/ml401/files/ml40x_usb.zip
   ```

   The mirror is a lead only; its files were not recovered.

9. DatasheetArchive search results expose an entry titled *Frameworks Reference Guide for the CY7C67300/CY7C67200 Family of Products*. This may be another route to the framework documentation, but the actual file and license still need verification.

### Negative results

- Exact web searches for `cy7c67200_300_hcd.c`, `cy7c67200_300_hcd_simple.c`, `hcd_irq_resumeX`, `de1_bios.asm`, and `ISRS.S` found the Infineon references but no independently downloadable source copies.
- Searches for `ml40x_usb.zip` found the historical URL but no live ZIP or verified archive copy.
- Searches scoped to Archive.org and the Wayback Machine did not return a captured CY3663 ISO or `ml40x_usb.zip` binary.
- A January 2026 Infineon support thread states that the product is discontinued and the software is no longer provided; the requester also reports that the old binary capture failed at Archive.org.
- GitHub repository searches through the connected API returned no repository directly named for CY3663 or CY7C67300. This does not rule out files hidden in unrelated repositories or unindexed archives.

## Recommended next search channels

1. **Owners of old development machines** — image disks or search installed directories for `C:\Cypress\USB\OTG-Host`.
2. **University FPGA course archives** — UIUC ECE projects, Xilinx ML403 labs, and Terasic DE2/DE2-115 course bundles.
3. **Old Xilinx ISE/EDK board-support media** — ML401/ML403/ML505 board CDs, WebPACK examples, and archived support downloads.
4. **Linux driver authors and companies** — Barco authors of the upstream `c67x00` driver may have retained the Cypress source tree used during the rewrite.
5. **Infineon/Cypress FAEs and former employees** — request archival media rather than current product support.
6. **Preservation communities** — Internet Archive software curators, Bitsavers, Vogons, WinWorld, BetaArchive, old FTP mirrors, and private driver collections.
7. **Package-content fingerprints** — search exact unique strings from known headers, binaries, and forum code rather than only product names.

## Intake and legal procedure

When an artifact is found:

1. Preserve the original archive unchanged.
2. Record origin, acquisition date, and SHA-256.
3. Inventory nested archives and all license/readme files.
4. Scan in an isolated environment before executing installers.
5. Extract filenames, symbols, strings, and object metadata.
6. Classify each item as redistributable, reference-only, or unknown.
7. Keep proprietary binaries/source out of the public repository unless distribution rights are established.
8. Convert useful behavior into original tests, source summaries, and compatibility fixtures.

## Completion criteria

Artifact recovery is considered materially successful when at least one of these is obtained:

- original CY16 GNUPro assembler/compiler/binutils binaries or source patches;
- `Common/ISRS.S` plus the canonical common header;
- the original Cypress Linux co-processor driver tree;
- CY4640's SCAN-to-LCP loader source;
- `ml40x_usb.zip` with a verifiable provenance chain;
- a complete CY3663 ISO/install tree.
