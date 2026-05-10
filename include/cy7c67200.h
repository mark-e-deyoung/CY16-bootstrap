#ifndef _CY7C67200_H
#define _CY7C67200_H

#include <stdint.h>

/* CPU and Memory Registers */
#define CPU_FLAGS_REG      (*(volatile uint16_t *)0xC000)
#define BANK_REG           (*(volatile uint16_t *)0xC002)
#define HW_REV_REG         (*(volatile uint16_t *)0xC004)
#define CPU_SPEED_REG      (*(volatile uint16_t *)0xC008)
#define POWER_CTL_REG      (*(volatile uint16_t *)0xC00A)
#define IRQ_EN_REG         (*(volatile uint16_t *)0xC00E)
#define XMEM_CTL_REG       (*(volatile uint16_t *)0xC03A)

/* HPI Registers */
#define HPI_IRQ_ROUTING_REG (*(volatile uint16_t *)0x0142)
#define HPI_SIE1_MSG_ADR    (*(volatile uint16_t *)0x0144)
#define HPI_SIE2_MSG_ADR    (*(volatile uint16_t *)0x0148)

/* Communication Mailbox (Standard BIOS location) */
#define COMM_CODE_ADDR      (*(volatile uint16_t *)0x01BC)
#define COMM_INT_NUM        (*(volatile uint16_t *)0x01C2)
#define COMM_R0             (*(volatile uint16_t *)0x01C4)

#endif
