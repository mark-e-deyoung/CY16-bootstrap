; BIOS-cooperative startup seed. Requires fuller assembler support before use.
.global main
.section .text
.global _start
_start:
    call main
.global _exit
_exit:
hang:
    jmp hang
