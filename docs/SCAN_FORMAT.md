# CY16 SCAN format bootstrap notes

The SCAN format lets EZ-OTG/EZ-Host BIOS or an external host parse records and perform actions such as copying code to RAM, writing control configuration, and calling or jumping to addresses.

## Common record prefix

```c
uint16_t signature;  // 0xC3B6, little-endian on disk
uint16_t length;     // bytes following opcode
uint8_t  opcode;
uint8_t  body[length];
```

Record size in bytes:

```text
length + 5
```

## Address-based records

COPY, JUMP, and CALL begin their body with a 16-bit little-endian address:

```c
uint16_t address;
uint8_t  payload[];
```

Known address-based opcodes:

```text
0x00 COPY
0x04 JUMP
0x05 CALL
```

For these records, `length` is two address bytes plus payload length.

## Configuration-space write

Official Infineon material documents opcode `0x09` with a different body shape:

```c
uint8_t  control_offset; // relative to 0xC000
uint16_t value;          // little-endian
```

The published example is:

```text
B6 C3 03 00 09 3A 22 22
```

which represents:

```text
WRITE_CONFIG address=0xC03A value=0x2222
```

An external HPI/co-processor loader must translate this operation into `COMM_WRITE_CTRL_REG`. It must not issue a direct HPI write to `0xC03A`, because processor-control space is outside AN6010's directly accessible HPI ranges.

`cy16-scan-decode` recognizes this record, and `make_config_record()` can generate it. Execution belongs in the companion DE2-115 loader after the LCP control-register argument/result convention is verified.

## Tooling

- `cy16-scan-decode` prints record boundaries, decoded target addresses, and payload summaries.
- `cy16-scanwrap` wraps a raw binary with a dummy alignment record, a setup stub, a call to the setup stub, a copy of the payload, and a call to the application entry.
- `tests/test_scan_config.py` anchors opcode `0x09` to the documented byte sequence.

## Known setup stub

```asm
mov [0xc03a], 0x23b3
ret
```

Words:

```text
0x07e7 0x23b3 0xc03a 0xcf97
```

This stub executes on the internal CY16 CPU. Its control-register write does not imply that the same address is directly writable by an external HPI master.

## Current safe-loader restrictions

The companion DE2-115 loader currently:

- restricts COPY destinations to internal RAM;
- requires even destination addresses and even payload sizes until unaligned read/modify/write is implemented;
- reads every copied block back and compares it byte-for-byte;
- recognizes WRITE_CONFIG but refuses to execute it until `COMM_WRITE_CTRL_REG` is implemented from a verified source;
- executes CALL/JUMP only when the caller explicitly enables control records.
