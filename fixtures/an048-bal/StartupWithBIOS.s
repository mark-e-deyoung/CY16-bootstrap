; Clean-room BIOS-cooperative startup fixture derived from AN048's described
; behavior. This file is intentionally retained as a compatibility target.
; It is not yet part of the green build because full BIOS-vector and interrupt
; syntax/semantics must be validated before hardware use.

.global _bal_fixture
.global _start
.section .text

_start:
    ; Replace the IDLER software-vector entry with the application entry point.
    ; AN048 identifies IDLER as vector 71, stored at vector * 2.
    mov [0x008e], _bal_fixture
    ret

; A complete compatibility version will also install a Timer0 ISR that saves
; flags, invokes BIOS PUSHALL/IDLE/POPALL services, reloads Timer0, executes
; STI, and returns. Add that sequence only with encoding and simulator tests.
