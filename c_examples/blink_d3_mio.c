/*
 * blink_d3_mio.c - Direct C Control of Onboard Bicolor LED D3 (PS MIO GPIO)
 * 
 * Target LEDs:
 * - D3 Red:   MIO37 -> Linux GPIO 549 (base 512 + 37)
 * - D3 Green: MIO38 -> Linux GPIO 550 (base 512 + 38)
 * 
 * Operates purely on the Zynq Processing System (PS) - NO FPGA BITSTREAM REQUIRED.
 * 
 * Compile: gcc -O3 -o blink_d3_mio blink_d3_mio.c
 * Run:     sudo ./blink_d3_mio
 */

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>
#include <string.h>

#define RED_GPIO    549  // MIO37
#define GREEN_GPIO  550  // MIO38

static int red_fd = -1;
static int green_fd = -1;

static void export_gpio(int gpio) {
    char path[64];
    snprintf(path, sizeof(path), "/sys/class/gpio/gpio%d", gpio);
    if (access(path, F_OK) != 0) {
        int fd = open("/sys/class/gpio/export", O_WRONLY);
        if (fd >= 0) {
            dprintf(fd, "%d", gpio);
            close(fd);
        }
    }
    snprintf(path, sizeof(path), "/sys/class/gpio/gpio%d/direction", gpio);
    int fd = open(path, O_WRONLY);
    if (fd >= 0) {
        write(fd, "out", 3);
        close(fd);
    }
}

static void sig_handler(int signo) {
    if (red_fd >= 0) write(red_fd, "0", 1);
    if (green_fd >= 0) write(green_fd, "0", 1);
    printf("\nCleaned up D3 LEDs. Exiting.\n");
    exit(0);
}

int main() {
    signal(SIGINT, sig_handler);
    signal(SIGTERM, sig_handler);

    export_gpio(RED_GPIO);
    export_gpio(GREEN_GPIO);

    red_fd = open("/sys/class/gpio/gpio549/value", O_WRONLY);
    green_fd = open("/sys/class/gpio/gpio550/value", O_WRONLY);

    if (red_fd < 0 || green_fd < 0) {
        perror("Error opening GPIO values (must be run with sudo)");
        return 1;
    }

    printf("==================================================\n");
    printf(" Antminer T9+ LED D3 Bicolor C Test (PS MIO GPIO)\n");
    printf("==================================================\n");
    printf("Blinking D3 alternating RED <-> GREEN (Ctrl+C to stop)...\n");

    for (int i = 0; i < 20; i++) {
        // Red ON, Green OFF
        write(red_fd, "1", 1);
        write(green_fd, "0", 1);
        printf("Cycle %02d/20: [ D3 RED   ]\r", i + 1);
        fflush(stdout);
        usleep(300000);

        // Red OFF, Green ON
        write(red_fd, "0", 1);
        write(green_fd, "1", 1);
        printf("Cycle %02d/20: [ D3 GREEN ]\r", i + 1);
        fflush(stdout);
        usleep(300000);
    }

    // Both OFF
    write(red_fd, "0", 1);
    write(green_fd, "0", 1);
    close(red_fd);
    close(green_fd);
    printf("\nTest finished. Both D3 channels turned off.\n");
    return 0;
}
