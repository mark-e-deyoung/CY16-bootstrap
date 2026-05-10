; Golden bootstrap fixture from Cypress scanwrap.c behavior.
.org 0x1000
.global _start
_start:
    mov [0xc03a], 0x23b3
    ret
