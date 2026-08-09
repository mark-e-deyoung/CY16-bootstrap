# Fingerprint-driven legacy artifact scanning

`cy16-artifact-scan` inventories local disks, backups, course-media trees, ZIP files, and TAR archives for exact CY16/CY7C67200/CY7C67300 recovery fingerprints. It does not extract archives or execute recovered software.

The scanner is intended for old development machines, copied Cypress installation trees, Xilinx board CDs, university course archives, backup drives, and preservation collections where broad web searches are ineffective.

## Command

```sh
cy16-artifact-scan \
  D:/old-development-media \
  E:/backups \
  -o private-recovery/scan-report.json \
  --content
```

On Linux or macOS:

```sh
cy16-artifact-scan \
  /mnt/old-disk \
  /srv/archive/board-cds \
  -o private-recovery/scan-report.json \
  --content
```

Defaults:

- recursively inspect regular files;
- inspect ZIP and TAR-family member names without extraction;
- do not scan file contents unless `--content` is supplied;
- limit content inspection and matched-member hashing to 16 MiB per file/member;
- emit deterministic JSON using schema `cy16-legacy-artifact-scan/v1`.

Use `--content-max-bytes` to change the per-file content limit and `--no-archives` when scanning a tree that contains very large or untrusted archive collections and only filesystem names are required.

## Fingerprint classes

### Exact filenames

The initial catalog includes:

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

Matching is case-insensitive so historical case variations are still found.

### Path fragments

The scanner looks for directory layouts cited by surviving Cypress/Infineon references:

```text
Cypress/USB/OTG-Host
Source/coprocessor/de_app
Source/coprocessor/linux/drivers/usb/cy7c67300
Common/ISRS.S
usbd/dedev/de1_bios.asm
```

Both slash styles are normalized for matching.

### Content symbols

With `--content`, small files and archive members are searched for exact ASCII symbols including:

```text
COMM_CTRL_REG_ADDR
COMM_CTRL_REG_DATA
COMM_LAST_DATA
COMM_READ_CTRL_REG
COMM_WRITE_CTRL_REG
hcd_irq_resume
DEFAULT_EOT
MAX_FRAME_BW
HUSB_SIE1_INIT_INT
HUSB_RESET_INT
CY3663
CY4640
cy16-elf-gcc
cy16-elf-as
cy16-elf-ld
cy16-elf-objdump
cy16-elf-objcopy
```

Content scanning is a fingerprint search, not source-code interpretation. A symbol match identifies a candidate for review; it does not establish authenticity, version, licensing, or compatibility.

## Report fields

Each match records:

- scanned root;
- filesystem location or archive member path;
- containing archive, when applicable;
- file/member type;
- fingerprint class and exact fingerprint;
- uncompressed size;
- SHA-256 when bytes were read;
- ZIP member CRC32 when available.

Archive members larger than the content limit may have `sha256: null`. Their member name, size, container, and ZIP CRC32 still provide useful intake evidence. Hash the original archive separately before extracting it in an isolated environment.

Unsafe archive-member paths are recorded with an `UNSAFE:` prefix. The scanner never extracts them.

## Privacy and publication

Reports contain absolute scan-root paths. Those paths can reveal usernames, drive layouts, organizations, or private archive names. Treat raw reports as private evidence unless they have been reviewed and sanitized.

Do not commit recovered proprietary bytes or complete private scan reports to the public repository. A public research note should normally include only:

- sanitized source or archive identifier;
- exact matching fingerprint;
- package/file version where established;
- file size and SHA-256;
- relevant nested paths;
- license/redistribution classification;
- acquisition date and provenance confidence.

## Recovery intake procedure

When a promising match is found:

1. Stop modifying the source media.
2. Record the device/archive identity and acquisition chain.
3. Hash the complete original file or disk image.
4. Copy it into an isolated analysis workspace.
5. Inventory nested archives and license/readme files before execution.
6. Scan installers and binaries with appropriate security tooling.
7. Determine whether the file is redistributable, reference-only, or legally uncertain.
8. Extract technical behavior into independently written tests and documentation.
9. Preserve exact filenames, version strings, compiler triplets, object metadata, and package manifests.
10. Update the dated recovery log and issue #7 without publishing restricted contents.

## Search discipline

A negative scan is meaningful only for the roots, options, and fingerprint catalog recorded in that report. It does not prove the artifact does not exist elsewhere.

Before repeating a scan, identify what changed:

- new media or backup root;
- additional fingerprint;
- content scanning enabled;
- higher content-size limit;
- newly supported archive format;
- decrypted or mounted filesystem that was previously inaccessible.

This prevents repeated broad searches from being mistaken for progress.

## Extending the fingerprint catalog

Add a fingerprint only when it comes from a traceable source such as:

- a Cypress/Infineon manual or accepted support answer;
- a surviving source implementation;
- a package listing or archived screenshot;
- a verified binary string or object symbol;
- a known installation path from an original development machine.

Every new fingerprint should have a corresponding note in `CY3663_ARTIFACT_WANTED.md` or the dated recovery log explaining where it came from and what it might recover.
