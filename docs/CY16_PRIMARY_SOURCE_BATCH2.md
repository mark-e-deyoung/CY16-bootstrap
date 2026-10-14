# CY16 original-manual reconciliation: memory and register controls

Evidence: CY16 Programmer's Guide v1.1, sections 1.3.3–1.3.7;
OTG-Host BIOS User's Manual v1.1, section 1.3.1 and figure 1-2.
This document records normalized facts, not proprietary tables.

## Register windows

REGBANK is memory mapped at 0xC002. A register Rn accesses
`(REGBANK & 0xFFE0) | (n << 1)` as a word address. The source
example maps R14 to 0x011C with REGBANK 0x0100. The existing
simulator's standalone 16-register list is not memory-window-aware.

## Flags and reset

FLAGS is mapped at 0xC000. The original manual shows five
low-order status bits: Z, C, O, S and interrupt enable I.
The processor's hardware reset entry is 0xFFF0. The guide
describes 48 hardware interrupt vectors. Instruction-specific
flag writes remain to be reconciled before changing the simulator.

## Memory profiles

The BIOS guide distinguishes a 64 KiB CPU-visible address space
from extended physical storage on EZ-Host. EZ-Host exposes
8 KiB external windows at 0x8000–0x9FFF and 0xA000–0xBFFF,
selected by registers 0xC018 and 0xC01A. EZ-OTG lacks this
external-memory interface. The manual warns that certain DMA
engines cannot safely transfer to external memory addresses.

Keep the existing flat test-memory model as a separate profile.
Do not assume that the same physical memory mapping applies to
EZ-OTG, EZ-Host, BIOS and standalone startup.

## Qualification gates

1. Verify the original page image and exact bitfield layouts.
2. Preserve original file hashes and model/BIOS applicability.
3. Introduce deterministic register-window, FLAGS and address
   translation tests, with negative controls.
4. Only then implement reversible profile-specific simulator changes.
5. Do not run DMA or physical hardware tests before the existing
   HPI RAM safety gate is independently satisfied.

Evidence limitations: register formula and page references were
checked in the Programmer's Guide source text; BIOS memory-map
figure was checked through extracted text, not a rendered figure.
No simulator or hardware conformance is claimed.
