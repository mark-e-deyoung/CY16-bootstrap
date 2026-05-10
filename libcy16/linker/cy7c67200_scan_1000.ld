/* Linker-script seed for historical GNUPro-compatible work. Not consumed by bootstrap tools yet. */
MEMORY {
  iram (rwx) : ORIGIN = 0x1000, LENGTH = 0x3000
  regs (rw)  : ORIGIN = 0xC000, LENGTH = 0x0100
}
SECTIONS {
  .text 0x1000 : { *(.text*) } > iram
  .rodata : { *(.rodata*) } > iram
  .data : { *(.data*) } > iram
  .bss : { *(.bss*) *(COMMON) } > iram
}
