/*
 * Clean-room AN048-shaped toolchain fixture.
 *
 * This is not Cypress BAL.c. It preserves the useful build characteristics:
 * freestanding 16-bit types, volatile MMIO, a callable entry point, raw-binary
 * placement, simulator validation, and SCAN packaging.
 */

typedef unsigned short uint16_t;

#define CY_XMEM_CTL_REG ((volatile uint16_t *)0xC03A)

uint16_t bal_fixture(void) {
    *CY_XMEM_CTL_REG = 0x23B3;
    return *CY_XMEM_CTL_REG;
}
