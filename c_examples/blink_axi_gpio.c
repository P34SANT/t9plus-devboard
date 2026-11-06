/*
 * blink_axi_gpio.c - Direct Hardware Register Control in C (Zynq AXI GPIO)
 * 
 * Maps physical AXI address 0x41200000 directly to virtual memory using mmap().
 * Provides bare-metal-style CMSIS/HAL register programming under Linux.
 * 
 * Target LEDs (Bank 35 PL):
 * - D5 Red:   Channel 1, Bit 0 (Pin M19)
 * - D6 Green: Channel 1, Bit 1 (Pin M17)
 * 
 * Compile: gcc -O3 -o blink_axi_gpio blink_axi_gpio.c
 * Run:     sudo ./blink_axi_gpio
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <signal.h>

#define AXI_GPIO_BASE   0x41200000
#define MAP_SIZE        0x1000

// Xilinx AXI GPIO Register Offsets (32-bit word indexing)
#define REG_DATA        0   // Offset 0x00: Channel 1 Data
#define REG_TRI         1   // Offset 0x04: Channel 1 Tri-state (0 = Output)

static volatile uint32_t *gpio = NULL;

void sig_handler(int signo) {
    if (gpio) {
        gpio[REG_DATA] = 0x00; // Turn off LEDs on exit
        munmap((void *)gpio, MAP_SIZE);
    }
    printf("\nCleaned up. Exiting.\n");
    exit(0);
}

int main() {
    signal(SIGINT, sig_handler);
    signal(SIGTERM, sig_handler);

    int fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (fd < 0) {
        perror("Error opening /dev/mem (must be run with sudo)");
        return 1;
    }

    // Map physical memory into user-space virtual pointer
    gpio = (volatile uint32_t *)mmap(
        NULL, MAP_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, AXI_GPIO_BASE
    );

    if (gpio == MAP_FAILED) {
        perror("mmap failed");
        close(fd);
        return 1;
    }

    printf("==================================================\n");
    printf(" Antminer T9+ AXI GPIO C Controller (No Python)\n");
    printf("==================================================\n");
    printf("Mapped AXI bus physical 0x%08X to virtual %p\n", AXI_GPIO_BASE, (void *)gpio);

    // Set all Channel 1 pins as outputs (0x00000000)
    gpio[REG_TRI] = 0x00000000;
    printf("GPIO Direction configured: Outputs.\n");
    printf("Toggling D5 Red <-> D6 Green (Press Ctrl+C to stop)...\n");

    for (int i = 0; i < 20; i++) {
        // Red ON, Green OFF
        gpio[REG_DATA] = 0x01;
        printf("Cycle %02d/20: [ D5 RED ON  ] [ D6 GREEN OFF ]\n", i + 1);
        usleep(300000); // 300 ms

        // Red OFF, Green ON
        gpio[REG_DATA] = 0x02;
        printf("Cycle %02d/20: [ D5 RED OFF ] [ D6 GREEN ON  ]\n", i + 1);
        usleep(300000);
    }

    gpio[REG_DATA] = 0x00; // All OFF
    munmap((void *)gpio, MAP_SIZE);
    close(fd);
    printf("Test finished. LEDs off.\n");
    return 0;
}
