#ifndef _CY16_H
#define _CY16_H

#include <stdint.h>
#include "cy7c67200.h"

static inline void cy16_write_word(uint16_t addr, uint16_t val) {
    *(volatile uint16_t *)addr = val;
}

static inline uint16_t cy16_read_word(uint16_t addr) {
    return *(volatile uint16_t *)addr;
}

static inline void cy16_halt(void) {
    __asm("ret");
}

#endif
