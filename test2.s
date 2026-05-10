.global _.L..1
_.L..1:
    .byte 97
    .byte 100
    .byte 100
    .byte 0
.global _.L..0
_.L..0:
    .byte 97
    .byte 100
    .byte 100
    .byte 0
.global _add
_add:
    mov r0, r0
    mov [--r15], r0
    mov r0, r1
    mov [--r15], r0
    mov r1, [r15++]
    mov r0, [r15++]
    add r0, r1
    mov [--r15], r0
    mov r0, [r15++]
    jmp .L.return.add
.L.return.add:
    ret

