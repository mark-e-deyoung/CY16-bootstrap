# CY16 C ABI v0

This ABI is a starting point for compiler development. It is not known to be binary-compatible with the original Cypress GNUPro ABI.

## Scalar model

```text
char              8-bit storage
signed char       8-bit storage, promoted to 16-bit for arithmetic
unsigned char     8-bit storage, promoted to 16-bit for arithmetic
short             16-bit
int               16-bit
unsigned          16-bit
pointer           16-bit
long              unsupported in v0, or explicitly 16-bit if enabled later
long long         unsupported in v0
float/double      unsupported in v0
```

## Register convention

```text
R0        return value, first scalar argument
R1        second scalar argument
R2        third scalar argument
R3        fourth scalar argument
R4-R7     scratch temporaries, caller-saved
R8-R14    pointer-capable registers, callee-saved in v1
R15       stack pointer, special push/pop behavior
```

## Calling convention

- First four 16-bit scalar arguments are passed in R0-R3.
- Additional arguments are passed on stack, v1 feature.
- Return value is in R0.
- Leaf functions may avoid stack use.
- Non-leaf functions preserve return linkage via CALL/RET.

## Volatile/MMIO

Volatile loads/stores must not be removed, combined, or reordered across other volatile operations. MMIO helpers should use explicit 8-bit or 16-bit access macros.

## Interrupt handlers

Interrupt handlers are out of v0 scope. Add a later `__attribute__((interrupt))` with a hardware-ISR prologue/epilogue that preserves flags and registers correctly.
