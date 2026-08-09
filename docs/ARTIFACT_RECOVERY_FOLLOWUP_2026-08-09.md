# Legacy artifact recovery follow-up — 2026-08-09

This record captures the exact-name follow-up search performed after the initial recovery catalog and scanner were created. It distinguishes source-path confirmation from actual artifact recovery.

## Search method

Exact public searches were run for:

```text
"de1_bios.asm" CY7C67200
"cy7c67200_300_hcd.c"
"cy7c67200_300_hcd_simple.c"
"ml40x_usb.zip"
```

The searches targeted publicly indexed source trees, mirrors, support records, and archive references. No recovered proprietary bytes were committed.

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

The exact-name searches did **not** locate an independently downloadable public copy of:

```text
de1_bios.asm
cy7c67200_300_hcd.c
cy7c67200_300_hcd_simple.c
ml40x_usb.zip
```

No file size, checksum, archive inventory, or immutable public object identifier was recovered for these items in this pass.

Search-engine results repeatedly led back to Infineon support records that reference the former CY3663 installation or to secondary mirrors of removed Xilinx pages. Do not mark any item as recovered based on those references.

## Scanner implications

The existing scanner catalog should retain or add the following exact fingerprints and spelling variants:

```text
de1_bios.asm
hcd_irq_resumeX
cy7c67200_300_hcd.c
cy7c67200_300_hcd_simple.c
cy7c67200_300_lcd.c
cy7c67200_300_lcp.c
MAX_FRAME_BW
DEFAULT_EOT
ml40x_usb.zip
SD1025
```

The installation-path fingerprint remains:

```text
Source\coprocessor\linux\drivers\usb\cy7c67300\usbd\dedev\de1_bios.asm
```

## Next recovery lanes

1. Search Internet Archive item metadata and CD/software collections using `CY3663`, `SD1025`, and `ml40x_usb.zip` as exact identifiers.
2. Search old university course mirrors for the full path fragment `usbd/dedev/de1_bios.asm` rather than only the basename.
3. Search package inventories, build logs, and backup indexes for `MAX_FRAME_BW`, `DEFAULT_EOT`, and `hcd_irq_resumeX` together.
4. Request attachment or archive metadata from Infineon before requesting bytes: original filename, size, timestamp, and checksum if retained.
5. Search Xilinx/AMD board-support media and old ISE/EDK installation trees for `SD1025` and `ml40x_usb.zip`.
6. Hash and inventory any candidate before extraction or execution; preserve licensing and redistribution status separately.
