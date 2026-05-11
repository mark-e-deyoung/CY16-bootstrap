# Bootstrap assembler subset

This package includes a deliberately small assembler. It exists to prove the project shape and provide the first golden validation fixture.

## Supported directives

```asm
.org 0x1000
.equ NAME, 0x1234
.global symbol
.globl symbol
.section .text
.text
.data
.bss
.short 0x1234
.word 0x1234
.byte 0x12, 0x34
.ascii "CY16"
.asciz "CY16"
.space 8
.skip 8, 0xff
```

`.bss` is accepted as a section marker. The bootstrap assembler emits a flat binary, so reserve explicit zero-filled bytes with `.space` or `.skip` when a binary image needs storage.

## Supported labels

```asm
_start:
    ret
```

## Supported instructions

```asm
ret
mov rN, immediate16
mov rN, rM
mov rN, [absolute_address]
mov [absolute_address], rN
mov [absolute_address], immediate16
mov [r8] through [r15]
mov [--r15], rN
mov rN, [r15++]
add, addc, sub, subb, cmp, and, test, or, xor
shr, shl, ror, rol, addi, subi
jmp, conditional jumps
call, conditional calls
```

The `mov [absolute_address], immediate16` form is currently implemented to match the Cypress `scanwrap.c` golden fixture:

```asm
mov [0xc03a], 0x23b3
ret
```

Expected words:

```text
0x07e7 0x23b3 0xc03a 0xcf97
```

## GNUPro compatibility conveniences

Registers may be written as either `rN` or `%rN`. Indirect register forms also accept `%rN`, for example:

```asm
mov %r0, 0x1234
mov [%r8], %r0
mov [--%r15], %r0
mov %r0, [%r15++]
```

`cy16-dis --gnupro` prints registers in `%rN` form.
