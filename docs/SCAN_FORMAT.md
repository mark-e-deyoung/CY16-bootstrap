# CY16 SCAN format bootstrap notes

The SCAN format lets EZ-OTG/EZ-Host BIOS or an external host parse records and perform actions such as copying code to RAM and calling/jumping to addresses.

## Bootstrap record layout

```c
uint16_t signature;  // 0xC3B6 little-endian on disk
uint16_t length;     // address field length + payload length
uint8_t  opcode;
uint16_t address;
uint8_t  payload[];
```

Record size in bytes:

```text
length + 5
```

Known opcodes:

```text
0x00 COPY
0x04 JUMP
0x05 CALL
```

## Tooling

- `cy16-scan-decode` prints record boundaries and payload summaries.
- `cy16-scanwrap` wraps a raw binary with a dummy alignment record, a setup stub, a call to the setup stub, a copy of the payload, and a call to the application entry.

## Known setup stub

```asm
mov [0xc03a], 0x23b3
ret
```

Words:

```text
0x07e7 0x23b3 0xc03a 0xcf97
```
