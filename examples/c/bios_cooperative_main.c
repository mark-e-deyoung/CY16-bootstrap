#include <stdint.h>
#include <stdbool.h>

/* Register addresses from cy7c67200.inc */
#define HW_REV_REG   (*(volatile uint16_t *)0xC004)
#define CPU_SPEED_REG (*(volatile uint16_t *)0xC008)

/**
 * bios_cooperative_main
 * 
 * Demonstrates a program that performs a simple logic loop
 * while remaining cooperative (not hanging the CPU).
 */
int main(void) {
    uint16_t rev = HW_REV_REG;
    
    /* Set CPU speed to 48MHz (if BIOS hasn't already) */
    CPU_SPEED_REG = 0x0000; 

    uint16_t count = 0;
    while (count < 100) {
        count++;
    }

    return (int)rev;
}
