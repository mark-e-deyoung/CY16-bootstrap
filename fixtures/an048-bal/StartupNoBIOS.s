; Clean-room startup fixture based on the behavior documented by AN048.
; The ROM BIOS has already performed reset-time initialization and loading.
; This entry point transfers control to the compiler-emitted _bal_fixture.

.org 0x1000
.global _start
.global _bal_fixture
.section .text
_start:
    jmp _bal_fixture
