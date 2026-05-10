.global _test_call
_test_call:
    mov r0, 5
    mov [--r15], r0
    mov r0, [r15++]
    call _(null)
    mov [--r15], r0
    mov r0, [r15++]
    jmp L_return_test_call
L_return_test_call:
    ret

.global _double_it
_double_it:
    mov r0, r0
    mov [--r15], r0
    mov r0, r0
    mov [--r15], r0
    mov r1, [r15++]
    mov r0, [r15++]
    add r0, r1
    mov [--r15], r0
    mov r0, [r15++]
    jmp L_return_double_it
L_return_double_it:
    ret

