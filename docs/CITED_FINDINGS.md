# Cited research findings for the CY16 compiler bootstrap

This file summarizes the findings that drive the bootstrap design. It is written as a source-indexed research note so an agent can trace each design decision back to the attached Cypress/Red Hat documents and source files.

## Source keys

- **[S1]** `cy16.pdf` — *GNUPro Toolkit User's Guide for Cypress Development*.
- **[S2]** `CY16 Programmers Guide.pdf` — *CY16 USB Host/Slave Controller/16-Bit RISC Processor Programmers Guide v1.1*.
- **[S3]** `CY16 Binary Utilities Reference.pdf`.
- **[S4]** `OTG-Host Boot Code Design.pdf`.
- **[S5]** `OTG-Host BIOS User Manual.pdf`.
- **[S6]** `scanwrap.c` — Cypress scanwrap source attached by the user.

## Findings

### 1. Historical toolchain shape: GNUPro / ELF / cy16-elf-* tools

The original Cypress development environment was a Red Hat GNUPro toolkit. The tools used triplet-style names such as `cy16-elf-gcc`, `cy16-elf-as`, `cy16-elf-ld`, `cy16-elf-gdb`, `cy16-elf-sid`, `cy16-elf-objcopy`, and `cy16-elf-objdump`. [S1]

**Design implication:** The bootstrap should imitate the historical shape, but not try to recreate the full ELF/GCC stack first. The v0 flow should be C -> CY16 assembly -> raw binary -> SCAN image. GNUPro/ELF compatibility is a later convergence track.

### 2. Compilation stages: preprocessing, compiling, assembling, linking

The GNUPro guide describes the normal staged GCC flow: preprocessing, compiling, assembling, and linking. It also identifies `.c`, `.s`, and `.S` source behavior. [S1]

**Design implication:** The chibicc-derived compiler should emit assembly (`-S`) first. The assembler, disassembler, simulator, and SCAN tooling are mandatory validation gates before full object/linker work.

### 3. CY16 ISA basics needed by assembler and backend

The Programmer's Guide says the CY16 uses a unified program/data memory space, is byte-addressable, supports byte moves and even-aligned word moves, has 16-bit general-purpose registers R0-R15, two register banks, and R8-R14 can serve as pointer registers while R15 is normally the stack pointer. [S2]

**Design implication:** The C ABI should use 16-bit `int`, 16-bit pointers, 8-bit `char` storage, and explicit byte/word load/store lowering. Pointer-heavy compiler code should prefer R8-R14 when register allocation becomes smarter.

### 4. Instruction format and addressing mode constraints

The Programmer's Guide states that general instructions contain four opcode bits, six source-operand bits, and six destination-operand bits. It documents byte/word addressing modifiers, immediate mode not being valid as a destination, and R15 restrictions for byte-wide indirect and auto-increment addressing. [S2]

**Design implication:** `cy16-as` must validate illegal operand modes; `cy16cc` must avoid generating byte-indirect through R15 or auto-increment through R15. Compiler stack code must treat R15 specially.

### 5. R15 stack behavior

R15 has special stack behavior: in indirect mode it pre-decrements on write and post-increments on read. Byte-wide indirect R15 operations are prohibited. The stack grows toward smaller addresses, CALL/INT push return addresses, and RET pops them. [S2]

**Design implication:** Stack frame generation should be delayed until tests cover R15 behavior. Early compiler v0 can use simple leaf functions before expanding to complex stack locals.

### 6. Hardware interrupt handling

The Programmer's Guide shows that hardware interrupts disable global interrupts and require user-supplied flag/register preservation, ending with restoring flags, `sti`, and `ret`. Software interrupts are effectively CALL-like and do not require the same hardware ISR template. [S2]

**Design implication:** `__attribute__((interrupt))` should not be implemented in v0. It should become a v1 feature after normal function ABI and stack handling are stable.

### 7. BIOS memory map and reset behavior

The BIOS manual gives a 64 KiB CY16 memory model with hardware/software vectors, register banks, HPI/mailbox area, LCP variables, BIOS stack, USB variables, user-code internal RAM beginning around `0x04A4`, memory-mapped registers at `0xC000-0xC0FF`, and BIOS ROM at `0xE000-0xFFFF`. It also describes BIOS reset: CPU speed initially divided down, PC set into ROM flow, R15 stack initialized to `0x0400`, memory control initialized, vectors set up, and BIOS services initialized. [S5]

**Design implication:** The simulator and linker scripts need CY7C67200/CY7C67300 memory profiles. Bootstrap examples should use `0x1000` or another safe load address and avoid trampling BIOS state unless intentionally standalone.

### 8. BIOS service stability rule

The BIOS manual warns users should use software vectors rather than arbitrary BIOS function addresses because arbitrary BIOS routines may move between BIOS versions. [S5]

**Design implication:** The runtime should expose BIOS software interrupt wrappers, not hard-coded calls into unknown ROM internals.

### 9. Minimal startup code

The Boot Code Design note says the Cypress startup code was reduced to the minimum needed to establish a C environment and call `main`. It shares the BIOS stack, performs no cleanup if `main` returns, and only needs `.bss` clearing if the program uses `.bss`. It also says to use `-nostartfiles` and link `startup.o` first when using the GNU driver. [S4]

**Design implication:** `libcy16` should provide separate `startup_bios.s`, `startup_nobios.s`, and `startup_sim.s`. The compiler should not assume a hosted libc or default CRT.

### 10. SCAN image requirement and SCANWRAP behavior

The Binary Utilities Reference states that EZ-OTG/EZ-Host BIOS can read programs from EEPROM, UART, USB, or ROM, and perform operations such as copying to RAM, initializing vectors, jumping, and calling absolute addresses. To do that, images need SCAN signatures compatible with Interrupt 67 (`SCAN_INT`). `SCANWRAP <in_file> <out_file> <base_address>` adds these headers, and the base address must match the linker script because SCANWRAP does not relocate code. [S3]

**Design implication:** `cy16-scanwrap` and `cy16-scan-decode` are first-class tools, not optional utilities. The compiler pipeline should produce raw binaries and then SCAN images.

### 11. BIOS Idle_Task must remain running for utilities

The Binary Utilities Reference states USB utilities rely on the EZ-OTG/EZ-Host BIOS and require the BIOS Idle_Task to be running; custom user code must not override it if those utilities are needed. [S3]

**Design implication:** The runtime must clearly distinguish BIOS-cooperative images from BIOS-takeover/standalone images.

### 12. Real scanwrap source provides a golden encoding fixture

The attached `scanwrap.c` help text says it takes the raw binary produced by `cy16-elf-objcopy -O binary` and adds SCAN_INT headers. It also states the base address must match the program's ORG location and that an optional call address may hook into the idle task chain and return to BIOS. The source explains an alignment issue: SCAN data must be word aligned even though the opcode is byte-sized, so a dummy header is inserted. [S6]

**Design implication:** The first assembler golden test is the `scanwrap.c` setup stub: `mov [0xc03a], 0x23b3 ; ret` -> words `0x07e7 0x23b3 0xc03a 0xcf97`. The bootstrap assembler/disassembler/simulator included here is anchored on that fixture.

## Recommended implementation doctrine

1. Build the assembler, disassembler, simulator, and SCAN tools before the compiler backend.
2. Vendor chibicc only after the tool validation path exists.
3. Emit assembly from the compiler in v0; do not emit ELF yet.
4. Keep the v0 C subset deliberately small.
5. Use simulator execution tests as the default compiler correctness gate.
6. Use SCAN image generation as the deployment packaging gate.
7. Keep Cypress-derived docs as references; avoid copying proprietary tables into public source.
