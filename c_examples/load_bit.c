/*
 * load_bit.c - High-Speed C FPGA Bitstream Loader (Linux fpga_manager)
 * 
 * Performs fast 16-bit word byte-swapping (conv=swab) in memory and streams
 * the binary directly into /sys/class/fpga_manager/fpga0/firmware.
 * 
 * Compile: gcc -O3 -o load_bit load_bit.c
 * Usage:   sudo ./load_bit <design.bit>
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <libgen.h>

#define CHUNK_SIZE 65536

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: sudo %s <design.bit>\n", argv[0]);
        return 1;
    }

    const char *bit_path = argv[1];
    int fin = open(bit_path, O_RDONLY);
    if (fin < 0) {
        perror("Error opening bitstream file");
        return 1;
    }

    struct stat st;
    fstat(fin, &st);
    printf("==> Reading %s (%ld bytes)...\n", bit_path, (long)st.st_size);

    // Extract base filename
    char *path_copy = strdup(bit_path);
    char *base = basename(path_copy);
    char fw_name[256];
    char dest_path[512];

    // Strip .bit suffix if present
    char *dot = strrchr(base, '.');
    if (dot) *dot = '\0';

    snprintf(fw_name, sizeof(fw_name), "%s_swapped.bin", base);
    snprintf(dest_path, sizeof(dest_path), "/lib/firmware/%s", fw_name);
    free(path_copy);

    mkdir("/lib/firmware", 0755);
    int fout = open(dest_path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fout < 0) {
        perror("Error creating firmware destination in /lib/firmware (must be root)");
        close(fin);
        return 1;
    }

    printf("==> Byte-swapping in memory -> %s...\n", dest_path);
    uint8_t buffer[CHUNK_SIZE];
    ssize_t n;
    while ((n = read(fin, buffer, CHUNK_SIZE)) > 0) {
        // Swap adjacent bytes in 16-bit words
        for (ssize_t i = 0; i < n - 1; i += 2) {
            uint8_t tmp = buffer[i];
            buffer[i] = buffer[i + 1];
            buffer[i + 1] = tmp;
        }
        write(fout, buffer, n);
    }
    close(fin);
    close(fout);

    // Stream into Linux FPGA Manager sysfs interface
    printf("==> Triggering FPGA configuration via /sys/class/fpga_manager/fpga0/firmware...\n");
    int fman = open("/sys/class/fpga_manager/fpga0/firmware", O_WRONLY);
    if (fman < 0) {
        perror("Error opening fpga_manager sysfs node");
        return 1;
    }

    write(fman, fw_name, strlen(fw_name));
    close(fman);

    usleep(200000); // 200 ms

    // Read back state
    char state[32] = {0};
    int fstate = open("/sys/class/fpga_manager/fpga0/state", O_RDONLY);
    if (fstate >= 0) {
        read(fstate, state, sizeof(state) - 1);
        close(fstate);
        // Strip trailing newline
        char *nl = strchr(state, '\n');
        if (nl) *nl = '\0';
    }

    if (strcmp(state, "operating") == 0) {
        printf("==> SUCCESS: FPGA fabric is PROGRAMMED and OPERATING! (State: %s)\n", state);
        printf("==> Check board: D1 Green LED (FPGA_DONE) should now be illuminated solid.\n");
        return 0;
    } else {
        fprintf(stderr, "==> WARNING: FPGA Manager reported unexpected state: '%s'\n", state);
        return 1;
    }
}
