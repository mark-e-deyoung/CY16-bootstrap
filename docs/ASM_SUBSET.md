# Bootstrap assembler subset

This package includes a deliberately small assembler. It exists to prove the project shape and provide the first golden validation fixture.

## Supported directives

```asm
.org 0x1000
.equ NAME, 0x1234
.global symbol
.section .text
.short 0x1234
.word 0x1234
.byte 0x12, 0x34
```

## Supported labels

```asm
_start:
    ret
```

## Supported instructions

```asm
ret
mov [absolute_address], immediate16
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

## Next instructions to add

1. `mov rN, imm`
2. `mov rN, [addr]`
3. `mov [addr], rN`
4. `add`, `sub`, `cmp`
5. `jmp`, conditional branches
6. `call`
7. `int`
8. stack forms through R15
