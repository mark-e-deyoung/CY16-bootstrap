#include <stdint.h>

uint16_t g_arr[10];

uint16_t test_ptr(void) {
    uint16_t *p = g_arr;
    *p = 0x1111;
    *(p + 1) = 0x2222;
    *(p + 2) = 0x3333;
    return g_arr[1] + g_arr[2]; // Should be 0x5555
}
