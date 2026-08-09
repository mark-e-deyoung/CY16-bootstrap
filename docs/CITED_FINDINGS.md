# Cited research findings for the CY16 compiler bootstrap

This file summarizes the findings that drive the bootstrap design. It is written as a source-indexed research note so an agent can trace each design decision back to the Cypress/Red Hat documents, source files, and external behavioral references. See `SOURCE_INDEX.md` for provenance, pins, licensing, and artifact-recovery status.

## Source keys

- **[S1]** `cy16.pdf` — *GNUPro Toolkit User's Guide for Cypress Development*.
- **[S2]** `CY16 Programmers Guide.pdf` — *CY16 USB Host/Slave Controller/16-Bit RISC Processor Programmers Guide v1.1*.
- **[S3]** `CY16 Binary Utilities Reference.pdf`.
- **[S4]** `OTG-Host Boot Code Design.pdf`.
- **[S5]** `OTG-Host BIOS User Manual.pdf`.
- **[S6]** `scanwrap.c` — Cypress scanwrap source supplied with the project material.
- **[S7]** AN048 — *Building an EZ-Host / EZ-OTG Project From Start to Finish*, Rev. *B.
- **[S8]** AN6010 — *Using HPI in Co-Processor Mode with EZ-Host/EZ-OTG*, Rev. **.
- **[S9]** Linux `drivers/usb/c67x00` — GPL behavioral reference derived from the older Cypress driver.
- **[S10]** `markubiak/sv-parametric-equalizer` — public DE2-115/Nios HPI and keyboard reference.
- **[S11]** `asciilifeform/Stierlitz` — CY7C67300/ML501 HPI state-machine reference.
- **[S12]** Official Infineon forum/KBA material identifying legacy CY3663 paths, files, and behavior.
- **[S13]** AMD/Xilinx Answer Record 31312 archival lead for `ml40x_usb.zip` and Cypress `SD1025`.

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

**Design implication:** `cy16-as` must validate illegal operand modes; `cy16cc` must avoid generating byte-indirect through R15 or illegal auto-increment forms. Compiler stack code must treat R15 specially.

### 5. R15 stack behavior

R15 has special stack behavior: in indirect mode it pre-decrements on write and post-increments on read. Byte-wide indirect R15 operations are prohibited. The stack grows toward smaller addresses, CALL/INT push return addresses, and RET pops them. [S2]

**Design implication:** Every stack form needs exact assembler and simulator tests. The compiler may use complex frames only after R15 behavior and nested-call linkage are proven.

### 6. Hardware interrupt handling

The Programmer's Guide shows that hardware interrupts disable global interrupts and require user-supplied flag/register preservation, ending with restoring flags, `sti`, and `ret`. Software interrupts are effectively CALL-like and do not require the same hardware ISR template. [S2]

**Design implication:** `__attribute__((interrupt))` remains gated on tested prologue/epilogue generation, the delayed effect of `STI`, and complete register-preservation rules.

### 7. BIOS memory map and reset behavior

The BIOS manual gives a 64 KiB CY16 memory model with hardware/software vectors, register banks, HPI/mailbox area, LCP variables, BIOS stack, USB variables, user-code internal RAM beginning around `0x04A4`, memory-mapped registers at `0xC000-0xC0FF`, and BIOS ROM at `0xE000-0xFFFF`. It also describes BIOS reset: CPU speed initially divided down, PC set into ROM flow, R15 stack initialized to `0x0400`, memory control initialized, vectors set up, and BIOS services initialized. [S5]

**Design implication:** The simulator and linker scripts need CY7C67200/CY7C67300 memory profiles. Bootstrap examples should use `0x1000` or another safe load address and avoid trampling BIOS state unless intentionally standalone.

### 8. BIOS service stability rule

The BIOS manual warns users should use software vectors rather than arbitrary BIOS function addresses because arbitrary BIOS routines may move between BIOS versions. [S5]

**Design implication:** The runtime should expose BIOS software-interrupt wrappers, not hard-coded calls into unknown ROM internals.

### 9. Minimal startup code

The Boot Code Design note says the Cypress startup code was reduced to the minimum needed to establish a C environment and call `main`. It shares the BIOS stack, performs no cleanup if `main` returns, and only needs `.bss` clearing if the program uses `.bss`. It also says to use `-nostartfiles` and link `startup.o` first when using the GNU driver. [S4]

**Design implication:** `libcy16` should provide separate `startup_bios.s`, `startup_nobios.s`, and `startup_sim.s`. The compiler should not assume a hosted libc or default CRT.

### 10. SCAN image requirement and SCANWRAP behavior

The Binary Utilities Reference states that EZ-OTG/EZ-Host BIOS can read programs from EEPROM, UART, USB, or ROM, and perform operations such as copying to RAM, initializing vectors, jumping, and calling absolute addresses. To do that, images need SCAN signatures compatible with Interrupt 67 (`SCAN_INT`). `SCANWRAP <in_file> <out_file> <base_address>` adds these headers, and the base address must match the linker script because SCANWRAP does not relocate code. [S3]

**Design implication:** `cy16-scanwrap` and `cy16-scan-decode` are first-class tools. The compiler pipeline should produce raw binaries and then SCAN images.

### 11. BIOS Idle_Task must remain running for utilities

The Binary Utilities Reference states USB utilities rely on the EZ-OTG/EZ-Host BIOS and require the BIOS Idle_Task to be running; custom user code must not override it if those utilities are needed. [S3]

**Design implication:** The runtime must clearly distinguish BIOS-cooperative images from BIOS-takeover/standalone images.

### 12. Real scanwrap source provides a golden encoding fixture

The supplied `scanwrap.c` help text says it takes the raw binary produced by `cy16-elf-objcopy -O binary` and adds SCAN_INT headers. It also states the base address must match the program's ORG location and that an optional call address may hook into the idle task chain and return to BIOS. The source explains an alignment issue: SCAN data must be word aligned even though the opcode is byte-sized, so a dummy header is inserted. [S6]

**Design implication:** The first assembler golden test is the `scanwrap.c` setup stub: `mov [0xc03a], 0x23b3 ; ret` -> words `0x07e7 0x23b3 0xc03a 0xcf97`. The assembler/disassembler/simulator are anchored on that fixture.

### 13. AN048 is an end-to-end toolchain acceptance target

AN048 documents separate assemble, compile, link, listing, object-to-binary, SCAN-wrap, and EEPROM-programming steps. It uses a program/link base of `0x1000` and requires the SCAN base to match. It also provides no-BIOS and BIOS-cooperative startup patterns. [S7]

**Design implication:** `fixtures/an048-bal` and `tests/test_an048_fixture.py` provide an original, clean-room compile -> assemble -> simulate -> SCAN acceptance path. Full historical compatibility still requires relocatable objects, linking, listings, and tested BIOS-cooperative startup.

### 14. Short branches and small immediates have high-risk boundary encodings

The Programmer's Guide defines relative branches as signed seven-bit word offsets (`-64..+63`). It also stores `n - 1` in the three-bit fields for shifts, rotates, `ADDI`, and `SUBI`. [S2]

**Design implication:** Add exact branch-boundary tests and exhaustive values 1-8 for these small-immediate instructions. Compiler emission is not conformant merely because ordinary examples assemble.

### 15. Historical assembler macros are not independent opcodes

The Programmer's Guide defines `INC`, `DEC`, `PUSH`, and `POP` as assembler macros expanding to `ADDI`, `SUBI`, and R15 `MOV` forms. [S2]

**Design implication:** Macro spellings belong in the assembler/parser layer. The simulator executes only canonical instructions, and disassembly may choose canonical or compatibility syntax explicitly.

### 16. External HPI direct access is not the same as internal CY16 MMIO

AN6010 defines the HPI ADDRESS port as write-only and limits direct HPI memory access to internal RAM, SIE windows, and BIOS ROM. Processor-control locations such as `0xC004`, `0xC008`, and `0xC00A` require LCP control-register commands. Internally executing CY16 code can still access the processor's MMIO map normally. [S8]

**Design implication:** Keep compiler volatile-MMIO tests separate from DE2-115 external-HPI tests. Do not weaken or alter the CY16 compiler because an external HPI master has a narrower direct-access window.

### 17. Linux is the strongest maintained HPI/LCP behavioral oracle

The upstream Linux driver records the four HPI ports, minimum cycle spacing, endian handling, mailbox synchronization, SIE initialization, reset service, TD pointers, and status handling. It states that it was derived from the older Cypress driver. [S9]

**Design implication:** Use Linux to cross-check behavior and create tests, but preserve the GPL boundary and independently derive definitions from vendor documents where practical.

### 18. The UIUC project is the strongest public DE2-115 implementation reference

The UIUC repository contains the DE2-115 HPI wrapper, Nios/Qsys metadata, a keyboard application, TD examples, and a large CY7C67200 header. [S10]

**Design implication:** Use it to compare pin assignments, polarity, bus latency, and transaction traces with the companion DE2-115 project. Treat Cypress/Terasic-derived files as provenance-sensitive rather than assuming the repository's public availability grants a permissive license.

### 19. Stierlitz is useful only at the HPI FSM layer

Stierlitz provides explicit multi-cycle HPI read/write states, output-enable control, read sampling, and mailbox handling for a CY7C67300 on an ML501. Its application protocol and board differ from this project. [S11]

**Design implication:** Use it as a state-machine and testbench reference, not as a USB host architecture or CY16 toolchain source. Its GPLv3 license also requires a deliberate reuse decision.

### 20. Legacy support pages expose precise recovery targets even when binaries are gone

Official Infineon answers identify `Common/ISRS.S`, `cy7C67200_300.h`, `Source/coprocessor/de_app`, the original Cypress Linux path, `de1_bios.asm`, CY4640's SCAN-to-LCP loader, and HCD tuning symbols. AMD/Xilinx AR 31312 points toward `ml40x_usb.zip` and Cypress `SD1025`, but the surviving AR evidence is only an archival lead. [S12] [S13]

**Design implication:** Maintain `CY3663_ARTIFACT_WANTED.md` as a search and intake ledger. Do not let unrecovered filenames become unverified implementation assumptions.

### 21. SCAN configuration writes require an LCP translation path

An Infineon KBA documents SCAN opcode `0x09` as a configuration-space write and explains that a co-processor loader should translate it into `COMM_WRITE_CTRL_REG`, rather than directly write the processor-control address over HPI. [S12]

**Design implication:** Extend SCAN decoding to preserve the opcode and add a verified loader translation in the DE2-115 project. This is required before claiming compatibility with general legacy scanwrapped images.

## Recommended implementation doctrine

1. Maintain assembler, disassembler, simulator, and SCAN tools as independent validation gates.
2. Emit assembly before adding object/ELF complexity.
3. Require source-derived boundary and negative tests, not only ordinary examples.
4. Keep CY16 internal-MMIO semantics separate from external-HPI accessibility.
5. Use simulator execution as the default compiler correctness gate.
6. Use SCAN decoding and packaging as the deployment gate.
7. Make AN048 the end-to-end integration fixture.
8. Pin and document every external behavioral reference.
9. Preserve license/source boundaries and avoid copying proprietary tables or source into public code.
10. Treat unrecovered CY3663/Xilinx filenames as artifact leads until inspected.
