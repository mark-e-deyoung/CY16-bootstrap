# Legacy artifact recovery follow-up — 2026-08-09

This record captures the exact-name follow-up searches performed after the initial recovery catalog and scanner were created. It distinguishes source-path or attachment-name confirmation from actual artifact recovery.

## Search method

Exact public searches were run for:

```text
"de1_bios.asm" CY7C67200
"cy7c67200_300_hcd.c"
"cy7c67200_300_hcd_simple.c"
"ml40x_usb.zip"
"BIOS_Release1.zip"
"MSC_EEPROM_scan_LCP_v2.bin"
"AN15484 - USB Flash Drive Controller Using SPI" zip
"susb1.s" attachment
"CY3663 CD-ROM Image v1.0"
"rID=14436" CY3663
```

The searches targeted publicly indexed source trees, mirrors, support records, migrated attachment labels, and archive references. No recovered proprietary bytes were committed.

## Confirmed high-value source paths

### `de1_bios.asm`

An Infineon/Cypress support answer identifies the historical CY3663 installation path:

```text
OTG-Host\Source\coprocessor\linux\drivers\usb\cy7c67300\usbd\dedev\de1_bios.asm
```

The answer specifically directs users to this file for SOF interrupt handling. The same thread confirms the CY7C67200 BIOS port-number mapping:

```text
Port 1A -> BIOS port 0
Port 2A -> BIOS port 2
```

Reference:

- https://community.infineon.com/t5/USB-hosts-hubs-transceivers/CY7C67200-EZ-OTG-HPI-Keyboard-Example/td-p/182887

Classification: **verified historical path and behavior lead; bytes not recovered**.

### HCD throughput constants

An Infineon knowledge-base article names two exact files and constants in the historical Linux co-processor driver:

```text
cy7c67200_300_hcd_simple.c : MAX_FRAME_BW
cy7c67200_300_hcd.c        : DEFAULT_EOT
```

The article states that the released driver reserved a large end-of-frame processing interval and that these constants controlled frame bandwidth and EOT duration.

Reference:

- https://community.infineon.com/t5/Knowledge-Base-Articles/Host-throughput-using-Linux-driver-may-be-low-due-to-EOT-time-slot/ta-p/250809

Classification: **verified filenames and symbol roles; bytes not recovered**.

### Insert/remove interrupt implementation

A second Infineon knowledge-base article identifies:

```text
hcd_irq_resumeX
cy7C67200_300_hcd.c
cy7C67200_300_lcd.c
```

It says `hcd_irq_resumeX` handles insert/remove interrupt processing and that the companion source configures interrupt-enable and HPI-routing registers.

The `*_lcd.c` spelling may be a migrated-article typo. Continue searching all of these variants:

```text
cy7c67200_300_lcd.c
cy7c67200_300_lcp.c
cy7C67200_300_lcd.c
cy7C67200_300_lcp.c
```

Reference:

- https://community.infineon.com/t5/Knowledge-Base-Articles/Enabling-of-USB-device-Insert-Remove-interrupt-to-the-Host-Port-Interface-HPI/ta-p/249066

Classification: **verified symbol/path lead with unresolved filename spelling; bytes not recovered**.

## Migrated attachment-name findings

### `susb1.s`

The current Infineon knowledge-base page still displays an attachment entry named exactly:

```text
susb1.s
```

The article instructs users to place it at:

```text
C:\Cypress\USB\OTG-Host\Source\stand-alone\common\susb1.s
```

and ties it to CY7C67300 errata points 10 and 11. The migrated page was listed as updated in April 2025, confirming that the attachment label survived the migration.

Reference:

- https://community.infineon.com/t5/Knowledge-Base-Articles/susb1-s-file/ta-p/249764

Classification: **current official attachment-name/path record; attachment bytes, size, checksum, and stable download object not recovered**.

### `BIOS_Release1.zip`

The current Infineon knowledge-base page for the EZ-Host/OTG software USB stack still displays an attachment entry named exactly:

```text
BIOS_Release1.zip
```

The article associates the material with the CY3663 frameworks examples and the CY4640 firmware USB host stack.

Reference:

- https://community.infineon.com/t5/Knowledge-Base-Articles/Software-USB-Stack-Implementation-For-EZ-Host-OTG/ta-p/250134

Classification: **current official attachment-name record; archive bytes, contents, size, checksum, and stable download object not recovered**.

### AN15484 support archive

The migrated forum record states that Cypress support supplied and authorized public posting of an archive named:

```text
AN15484 - USB Flash Drive Controller Using SPI (EZ-Host USB Host).zip
```

The outer ZIP reportedly contained a RAR support archive, including:

```text
MSC_EEPROM_scan_LCP_v2.bin
```

A separate 2020 support thread confirms this installed/source-tree path:

```text
AN15484\Memory Stick Code CY4640\sbc\msc_api\MSC_EEPROM_scan_LCP_v2.bin
```

Historical ticket and record identifiers remain:

```text
support ticket: 1817818920
old forum rID:  71172
```

References:

- https://community.infineon.com/t5/USB-low-full-high-speed/Does-anybody-have-file-MSC-EEPROM-scan-LCP-v2-bin/td-p/63946
- https://community.infineon.com/t5/USB-hosts-hubs-transceivers/CY7C6300-EZ-Host-Programm-MSC-EEPROM-scan-LCP-v2-bin-is-Not-working-After/td-p/169060
- https://community.infineon.com/t5/USB-low-full-high-speed/Can-t-get-started-with-CY7C67300-EZHOST/td-p/127236

Classification: **official historical attachment title, permission statement, binary name, and path confirmed; no attachment bytes or immutable attachment object recovered**.

The same historical discussion distinguishes the normal CY4640 co-processor build output:

```text
C:\Cypress\USB\OTG-Host\Source\stand-alone\sbc\msc_api
make clean wrap
coproc_api_scan.bin
```

from the EEPROM-oriented AN15484 image. These must remain separate fingerprints and must not be treated as interchangeable artifacts.

## Current CY3663 availability check

A January 2026 Infineon support thread identifies the former package as:

```text
CY3663 CD-ROM Image v1.0
```

and points to the former Cypress document slug:

```text
/documentation/software-and-drivers/cy3663-cd-rom-image-v10
```

The requester reported that the archive capture did not preserve a working payload. Infineon support responded that the discontinued product's software is no longer provided.

Reference:

- https://community.infineon.com/t5/USB-hosts-hubs-transceivers/Where-can-I-find-the-old-software-for-the-EZ-Host-CY7C67300-CY3663/td-p/1172299

An older 2012 thread confirms that the historical direct download identifier was:

```text
http://www.cypress.com/?rID=14436
```

and that the image successfully installed on Vista even though it failed on Windows 7 in that user's test. This establishes that the payload existed at that identifier in 2012, but does not recover it now.

Classification: **official current unavailability statement plus historical package title/URL identifiers; CD image not recovered**.

## Xilinx board-package lead

A surviving mirror of an old Xilinx answer record identifies these historical resources for ML40x, ML50x, and ML605 boards:

```text
Cypress design/support package: SD1025
Xilinx board archive: ml40x_usb.zip
Historical URL: http://www.xilinx.com/products/boards/ml401/files/ml40x_usb.zip
```

Reference mirror:

- https://chipdebug.com/forum_tag/socs/page/218

The mirror is not an authoritative archive and did not provide the ZIP bytes or a hash. Treat the filename, former URL, and SD1025 identifier as recovery fingerprints only.

Classification: **secondary historical lead; archive not recovered**.

## Negative results

The exact-name and attachment-path searches did **not** locate an independently downloadable, verifiable public copy of:

```text
de1_bios.asm
cy7c67200_300_hcd.c
cy7c67200_300_hcd_simple.c
ml40x_usb.zip
susb1.s
BIOS_Release1.zip
AN15484 - USB Flash Drive Controller Using SPI (EZ-Host USB Host).zip
MSC_EEPROM_scan_LCP_v2.bin
CY3663 CD-ROM Image v1.0
```

No trustworthy file size, checksum, complete archive inventory, or immutable public attachment/object identifier was recovered for these items in this pass.

The Infineon pages expose attachment display names in indexed text, but the searches did not expose a stable attachment download URL suitable for preservation or verification. Search-engine results repeatedly led back to migrated support records, removed Cypress pages, or secondary mirrors. Do not mark any item as recovered based on those references.

## Scanner implications

The scanner catalog already covers many of the exact names above. It should retain or add these additional exact fingerprints and spelling variants:

```text
de1_bios.asm
hcd_irq_resume
hcd_irq_resumeX
cy7c67200_300_hcd.c
cy7c67200_300_hcd_simple.c
cy7c67200_300_lcd.c
cy7c67200_300_lcp.c
MAX_FRAME_BW
DEFAULT_EOT
ml40x_usb.zip
SD1025
CY3663 CD-ROM Image v1.0
rID=14436
rID=71172
```

The installation-path fingerprints remain:

```text
Source\coprocessor\linux\drivers\usb\cy7c67300\usbd\dedev\de1_bios.asm
Source\stand-alone\common\susb1.s
AN15484\Memory Stick Code CY4640\sbc\msc_api
```

## Next recovery lanes

1. Request attachment metadata from Infineon using article/thread IDs and exact attachment names before requesting bytes: original filename, stored size, timestamp, checksum, and internal attachment identifier.
2. Search Internet Archive item metadata and software/CD collections using `CY3663 CD-ROM Image v1.0`, `rID=14436`, `SD1025`, and `ml40x_usb.zip` as exact identifiers.
3. Search old university course mirrors for the full path fragment `usbd/dedev/de1_bios.asm` rather than only the basename.
4. Search package inventories, build logs, and backup indexes for `MAX_FRAME_BW`, `DEFAULT_EOT`, and `hcd_irq_resumeX` together.
5. Search Xilinx/AMD board-support media and old ISE/EDK installation trees for `SD1025` and `ml40x_usb.zip`.
6. Search personal/organizational backups using the local scanner for `BIOS_Release1.zip`, `susb1.s`, the AN15484 archive title, and the historical Cypress installation paths.
7. Hash and inventory any candidate before extraction or execution; preserve licensing and redistribution status separately.
