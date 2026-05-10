#include <stdint.h>

uint16_t read_hwrev(void) {
    return *(volatile uint16_t *)0xC004;
}
