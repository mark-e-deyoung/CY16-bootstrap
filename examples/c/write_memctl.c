#include <stdint.h>

#define XMEM_CTL_REG (*(volatile uint16_t *)0xC03A)

/**
 * write_memctl
 * 
 * Demonstrates basic MMIO write to the memory control register.
 * Value 0x23b3 is the Cypress golden fixture value.
 */
void write_memctl(void) {
    XMEM_CTL_REG = 0x23b3;
}
