; Standalone startup seed. Requires stack initialization policy and fuller assembler support.
.equ STACK_TOP, 0x0400
.global main
.section .text
.global _start
_start:
    ; TODO: initialize r15 when assembler supports register/immediate mov.
    call main
hang:
    jmp hang
