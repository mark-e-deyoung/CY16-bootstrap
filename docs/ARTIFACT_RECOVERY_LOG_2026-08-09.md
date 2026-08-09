# Legacy artifact recovery log — 2026-08-09

This log records what was established during the current research pass, what was not recovered, and which new search mechanisms were added. It distinguishes verified source references from artifact possession.

## Scope

Targets:

- CY3663 OTG-Host development software and CD/install tree;
- CY4640 v1.1+ source and SCAN-to-LCP loader;
- AN15484 mass-storage support package and EEPROM image;
- Xilinx `ml40x_usb.zip` and related ML40x/ML50x/ML605 packages;
- canonical common headers, framework fixes, and `ISRS.S`;
- historical Cypress Linux co-processor source;
- original CY16 GNUPro binaries, patches, and object/ABI evidence;
- framework documentation and examples.

No recovered proprietary package, support attachment, installer, or binary was committed during this pass.

## Follow-up findings: AN15484 support attachment

### What the migrated support record establishes

A migrated Cypress/Infineon forum thread states that Cypress customer support supplied an AN15484 support archive and authorized the recipient to post it publicly. The post names the attachment exactly as:

```text
AN15484 - USB Flash Drive Controller Using SPI (EZ-Host USB Host).zip
```

The same post says:

- the outer ZIP contained the RAR archive supplied by customer support;
- the support files included `MSC_EEPROM_scan_LCP_v2.bin`;
- a separate October 2010 copy of the application note was newer than the August 2007 copy inside the support archive;
- the poster used the binary on a custom board that booted, enumerated a USB flash drive, and produced a directory listing.

This is a high-confidence historical attachment lead. It is **not** recovered software: this project has not obtained the ZIP, nested RAR, application note attachment, or binary bytes, and has no hash or directory listing for them.

### Independent path confirmation

A 2020 Infineon support thread records this local path for the same binary:

```text
..\AN15484\Memory Stick Code CY4640\sbc\msc_api\MSC_EEPROM_scan_LCP_v2.bin
```

That confirms that the AN15484/CY4640 support tree and binary were still circulating in 2020. It does not establish that every CY4640 installer contained the file.

### Related CY4640 build distinction

A 2012 support thread records the ordinary installed CY4640 source path:

```text
C:\Cypress\USB\OTG-Host\Source\stand-alone\sbc\msc_api
```

Running `make clean wrap` there reportedly produced:

```text
coproc_api_scan.bin
```

The poster explicitly distinguished that co-processor-boot image from the EEPROM-oriented `MSC_EEPROM_scan_LCP_v2.bin` expected by AN15484. The scanner therefore treats both names and both path layouts as separate fingerprints.

The same thread records:

- Cypress support ticket `1817818920`;
- historical CY3663 download ID `rID=14436`;
- `cy_dev.inf` and `cyusbgen.sys` under `C:\Cypress\USB\OTG-Host\Drivers`;
- CY3663 installation success on Vista but not Windows 7 in that user's environment;
- absence of the AN15484 `msc_api` source and EEPROM binary from that installed CY3663 tree.

These are historical recovery clues, not recommendations to install obsolete drivers on a current system.

### Attachment-object status

Public search found the migrated post text, attachment display name, and support-ticket trail, but did not expose a downloadable attachment URL, immutable attachment identifier, file size, CRC, or hash. Exact GitHub and general public searches for the attachment title and `MSC_EEPROM_scan_LCP_v2.bin` did not recover an independent copy.

Next targeted request:

- Infineon migrated thread ID `63946`;
- old Cypress forum record `rID=71172`;
- exact attachment title above;
- support ticket `1817818920`;
- request attachment metadata or hash before requesting large bytes;
- ask whether migrated attachment storage can be restored or exported.

Do not mark the artifact recovered until the bytes are obtained, hashed, inventoried, and provenance/licensing are classified.

## Follow-up findings: `susb1.s` framework fix

An Infineon knowledge-base record says the `susb1.s` file was attached to the interaction and should be placed at:

```text
C:\Cypress\USB\OTG-Host\Source\stand-alone\common\susb1.s
```

The record ties the file to CY7C67300 errata points 10 and 11 and to the CY3663 framework installation. Related framework references identify useful neighboring fingerprints:

```text
fwxcfg.h
fwxmain.c
usb_init
FIX_USB1_EP1
FWX_SERIAL_EEPROM
```

The project has not recovered the attachment bytes. The migrated knowledge-base text is a high-value attachment/path lead only.

A separate Infineon knowledge-base article about the software USB stack also exposes an attachment named:

```text
BIOS_Release1.zip
```

That attachment may contain framework or firmware material relevant to the host stack. It is now a scanner fingerprint, but its bytes and contents have not been recovered or verified here.

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

### Host/SIE/HCD and framework symbols

```text
hcd_irq_resume
DEFAULT_EOT
MAX_FRAME_BW
HUSB_SIE1_INIT_INT
HUSB_RESET_INT
usb_init
FIX_USB1_EP1
FWX_SERIAL_EEPROM
```

These target the old Cypress HCD, BIOS interrupt, standalone framework, and USB1 errata-fix implementations rather than generic USB source trees.

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
MSC_EEPROM_scan_LCP_v2.bin
coproc_api_scan.bin
AN15484 - USB Flash Drive Controller Using SPI (EZ-Host USB Host).zip
scanwrp2
scanwrap.c
ezhost.c
cy_dev.inf
cyusbgen.sys
susb1.s
fwxcfg.h
fwxmain.c
BIOS_Release1.zip
BAL.ld
StartupNoBIOS.s
StartupWithBIOS.s
```

The `*_lcd.c` spelling remains a lead because the historical support answer may contain a typo; likely `*_lcp.c` and nearby initialization variants remain in the catalog as well.

### Installation/package paths

```text
C:\Cypress\USB\OTG-Host
C:\Cypress\USB\OTG-Host\Drivers
Source\coprocessor\de_app
Source\coprocessor\linux\drivers\usb\cy7c67300
Source\stand-alone\sbc\msc_api
AN15484\Memory Stick Code CY4640\sbc\msc_api
Source\stand-alone\common\susb1.s
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

Multiple official/community references establish that the development kit installed the OTG-Host source tree, GNUPro tools, frameworks, drivers, and examples. A January 2026 Infineon answer states that the discontinued product is no longer supported and the software is no longer provided through normal support. No complete ISO, installer, or verified install tree was recovered during this pass.

### CY4640 and AN15484

Official/community material identifies CY4640 v1.1+ as a reference for externally parsing standalone SCAN images and translating configuration writes to `COMM_WRITE_CTRL_REG`. It also points to standalone mass-storage source, `make wrap`, `msc_scan.bin`, and `coproc_api_scan.bin`.

The migrated AN15484 thread materially improves this lead by naming an authorized public support ZIP, nested RAR, EEPROM image, and exact path. No complete CY4640 source package, AN15484 support archive, or installer was recovered during this pass.

### Xilinx `ml40x_usb.zip`

A surviving mirror of AMD/Xilinx Answer Record 31312 names `ml40x_usb.zip` and the Cypress SD1025 package location. The original archive was not recovered, and the mirror description alone is not treated as authoritative package content.

### Framework attachments

The migrated Infineon knowledge base names attachments `susb1.s` and `BIOS_Release1.zip`. Neither attachment object was recovered or hashed in this pass.

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
MSC_EEPROM_scan_LCP_v2.bin
AN15484 - USB Flash Drive Controller Using SPI (EZ-Host USB Host).zip
susb1.s
BIOS_Release1.zip
```

This is a negative result for the public search channels used during this pass, not proof that the files no longer exist. In several cases the migrated page explicitly says an attachment existed even though current search did not expose its bytes.

## Archive/preservation status

- No verified Internet Archive item containing the complete CY3663 media was established.
- No verified Wayback capture of `ml40x_usb.zip` bytes was established.
- No directly named GitHub repository for CY3663, the full CY7C67300 kit, or the AN15484 support bundle was found through exact-name searches.
- No downloadable migrated attachment object was resolved for the AN15484 ZIP, `susb1.s`, or `BIOS_Release1.zip`.
- This does not exclude files embedded in unrelated repositories, releases, issue attachments, course bundles, disk images, private support exports, or unindexed archives.

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

The follow-up pass adds AN15484 attachment/package paths, old Cypress drivers, and framework/errata-fix files to the tested catalog.

This makes old local disks and backup collections a first-class search channel rather than depending exclusively on web indexing.

## Recommended next media and preservation sources

In priority order:

1. Infineon community/support attachment export for thread `63946`, old `rID=71172`, and ticket `1817818920`.
2. Any old Windows system or backup that may have `C:\Cypress\USB\OTG-Host`.
3. User backups containing the AN15484/CY4640 `Memory Stick Code` tree.
4. University course-media archives for DE2/DE2-115, ML401/ML403, MicroBlaze, PowerPC, or USB-host labs.
5. Xilinx ISE/EDK board CDs and downloaded board-support directories.
6. Old engineering file servers, optical-media collections, and personal backup drives.
7. Disk images or source archives retained by Linux `c67x00` contributors and their former employers.
8. Media retained by authors of the surviving UIUC/Terasic project.
9. Preservation communities that can search private software indexes by exact filename, attachment title, CRC, or old forum ID rather than public page text.

## Contact discipline

Potential contacts should be approached individually with a narrow archival request:

- exact package/file sought;
- historical date/product context;
- migrated and old thread identifiers;
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
5. For migrated attachments, record thread ID, attachment display name, platform attachment identifier, and any platform-supplied metadata.
6. Locate license, readme, release-note, and version files.
7. Scan in an isolated environment.
8. Classify redistribution rights.
9. Compare files against existing public/reference implementations.
10. Extract facts into original tests and documentation.
11. Keep restricted bytes outside the public repository unless rights are clear.

## Current conclusion

The public research did not recover the legacy bytes, but it materially narrowed three actionable attachment targets:

1. the authorized AN15484 support ZIP containing a nested RAR and `MSC_EEPROM_scan_LCP_v2.bin`;
2. the attached `susb1.s` USB1 errata/framework fix;
3. the attached `BIOS_Release1.zip` software-stack package.

The highest-leverage next actions are a targeted migrated-attachment export request and scanning old local media with the expanded exact fingerprint catalog. Until bytes, hashes, and provenance exist, all three remain leads rather than recovered artifacts.
