# Legacy artifact recovery log — 2026-08-09

This log records what was established during the current research pass, what was not recovered, and which new search mechanisms were added. It distinguishes verified source references from artifact possession.

## Scope

Targets:

- CY3663 OTG-Host development software and CD/install tree;
- CY4640 v1.1+ source and SCAN-to-LCP loader;
- Xilinx `ml40x_usb.zip` and related ML40x/ML50x/ML605 packages;
- canonical common headers and `ISRS.S`;
- historical Cypress Linux co-processor source;
- original CY16 GNUPro binaries, patches, and object/ABI evidence;
- framework documentation and examples.

No recovered proprietary package or installer was committed during this pass.

## Verified source-derived fingerprints

The following exact fingerprints are supported by the reviewed manuals, Infineon/Cypress community material, or surviving implementations and have been added to the local scanner catalog.

### Control-register/LCP symbols

```text
COMM_CTRL_REG_ADDR
COMM_CTRL_REG_DATA
COMM_LAST_DATA
COMM_READ_CTRL_REG
COMM_WRITE_CTRL_REG
```

The OTG-Host BIOS User Manual establishes the first four command-related names and shared-memory roles. `COMM_LAST_DATA` is an additional implementation/string fingerprint that may occur in historical BIOS or loader sources.

### Host/SIE/HCD symbols

```text
hcd_irq_resume
DEFAULT_EOT
MAX_FRAME_BW
HUSB_SIE1_INIT_INT
HUSB_RESET_INT
```

These target the old Cypress HCD and BIOS interrupt implementation rather than generic USB source trees.

### Toolchain strings

```text
cy16-elf-gcc
cy16-elf-as
cy16-elf-ld
cy16-elf-objdump
cy16-elf-objcopy
```

These identify the historical GNUPro target environment, build logs, scripts, registry/config files, and binary distributions even when package names have been lost.

### Exact files and package names

```text
ISRS.S
cy7c67200_300.h
cy7c67200_300_hcd.c
cy7c67200_300_hcd_simple.c
cy7c67200_300_lcp.c
cy7c67200_300_lcd.c
de1_bios.asm
ml40x_usb.zip
msc_scan.bin
scanwrp2
scanwrap.c
BAL.ld
StartupNoBIOS.s
StartupWithBIOS.s
```

The `*_lcd.c` spelling remains a lead because the historical support answer may contain a typo; likely `*_lcp.c` and nearby initialization variants remain in the catalog as well.

### Installation/package paths

```text
C:\Cypress\USB\OTG-Host
Source\coprocessor\de_app
Source\coprocessor\linux\drivers\usb\cy7c67300
Common\ISRS.S
usbd\dedev\de1_bios.asm
```

These are useful for scanning full disk images, backups, Windows search indexes, old course archives, and nested board-support packages.

## Confirmed public references

### Linux `c67x00`

The maintained Linux driver remains the strongest public behavioral reference for HPI/LCP and host scheduling. The inspected low-level driver does not contain `COMM_READ_CTRL_REG` or `COMM_WRITE_CTRL_REG`, so it does not recover those command helpers.

### UIUC/Terasic DE2-115 project

The surviving project includes the DE2-115 HPI wrapper, Nios software, a large Cypress-derived header, and USB host examples. The inspected USB source uses direct HPI operations and `COMM_RESET`; no implementation of the two control-register LCP commands was found in that file.

### Stierlitz

The ML501/CY7C67300 project remains useful for multi-phase HPI RTL timing and mailbox sequencing. It is not a general USB-host stack and does not substitute for the missing Cypress packages.

## Confirmed package leads not recovered

### CY3663

Multiple official/community references establish that the development kit installed the OTG-Host source tree, GNUPro tools, frameworks, drivers, and examples. No complete ISO, installer, or verified install tree was recovered during this pass.

### CY4640

Official/community material identifies CY4640 v1.1+ as a reference for externally parsing standalone SCAN images and translating configuration writes to `COMM_WRITE_CTRL_REG`. It also points to standalone mass-storage source, `make wrap`, and `msc_scan.bin`. No complete CY4640 source package or installer was recovered during this pass.

### Xilinx `ml40x_usb.zip`

A surviving mirror of AMD/Xilinx Answer Record 31312 names `ml40x_usb.zip` and the Cypress SD1025 package location. The original archive was not recovered, and the mirror description alone is not treated as authoritative package content.

## Exact-name public search results

Searches for the following names located source references and forum/KBA mentions but no independently downloadable verified source copies:

```text
cy7c67200_300_hcd.c
cy7c67200_300_hcd_simple.c
hcd_irq_resumeX
de1_bios.asm
ISRS.S
ml40x_usb.zip
scanwrp2
msc_scan.bin
```

This is a negative result for the public search channels used during this pass, not proof that the files no longer exist.

## Archive/preservation status

- No verified Internet Archive item containing the complete CY3663 media was established.
- No verified Wayback capture of `ml40x_usb.zip` bytes was established.
- No directly named GitHub repository for CY3663 or the full CY7C67300 kit was found through repository-name searches.
- This does not exclude files embedded in unrelated repositories, releases, issue attachments, course bundles, disk images, or unindexed archives.

## New recovery capability added

A standard-library-only scanner was added on branch `agent/issue-7-artifact-fingerprint-recovery`:

```text
cy16-artifact-scan
```

It can:

- recursively inventory files;
- inspect ZIP and TAR member names without extraction;
- optionally scan small file/member contents for exact ASCII fingerprints;
- hash matched regular files and small archive members;
- record ZIP member CRC32 values;
- identify unsafe archive member paths without extracting them;
- emit deterministic `cy16-legacy-artifact-scan/v1` JSON.

This makes old local disks and backup collections a first-class search channel rather than depending exclusively on web indexing.

## Recommended next media sources

In priority order:

1. Any old Windows system or backup that may have `C:\Cypress\USB\OTG-Host`.
2. University course-media archives for DE2/DE2-115, ML401/ML403, MicroBlaze, PowerPC, or USB-host labs.
3. Xilinx ISE/EDK board CDs and downloaded board-support directories.
4. Old engineering file servers, optical-media collections, and personal backup drives.
5. Disk images or source archives retained by Linux `c67x00` contributors and their former employers.
6. Media retained by authors of the surviving UIUC/Terasic project.
7. Preservation communities that can search private software indexes by exact filename or CRC rather than public page text.

## Contact discipline

Potential contacts should be approached individually with a narrow archival request:

- exact package/file sought;
- historical date/product context;
- preservation/research purpose;
- request for hashes or directory listing before transferring large media;
- no request to violate employer confidentiality or redistribution terms.

Do not publish private email addresses, phone numbers, or personal details in this repository. Record public project/profile paths and outreach status only.

## Intake requirements for any future recovery

Before executing or importing anything:

1. Preserve the original bytes unchanged.
2. Record acquisition source, date, and provenance chain.
3. Compute SHA-256 for the outer archive/media image.
4. Inventory nested files and archives.
5. Locate license, readme, release-note, and version files.
6. Scan in an isolated environment.
7. Classify redistribution rights.
8. Compare files against existing public/reference implementations.
9. Extract facts into original tests and documentation.
10. Keep restricted bytes outside the public repository unless rights are clear.

## Current conclusion

The public research materially improved the fingerprint catalog and command semantics but did not recover the complete legacy packages. The highest-leverage next action is scanning old local media and targeted archive indexes with the exact fingerprints now encoded in `cy16-artifact-scan`.
