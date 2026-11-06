#!/bin/bash
set -e

# build_initramfs.sh - Build minimal BusyBox trampoline initramfs for T9+ PYNQ devboard
# Automatically mounts /dev/mmcblk0p2 and executes switch_root into PYNQ Ubuntu 22.04

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUSYBOX="${SCRIPT_DIR}/boot/uramdisk_src/busybox-armv7"
OUTPUT="${SCRIPT_DIR}/boot/uramdisk.image.gz"

if [ ! -f "$BUSYBOX" ]; then
    echo "ERROR: BusyBox binary not found at $BUSYBOX"
    exit 1
fi

echo "==> Building T9+ trampoline initramfs..."
python3 "${SCRIPT_DIR}/boot/build_uramdisk.py"

if [ -f "$OUTPUT" ]; then
    SIZE=$(stat -c%s "$OUTPUT" 2>/dev/null || stat -f%z "$OUTPUT")
    echo "==> Success: $OUTPUT ($SIZE bytes)"
else
    echo "ERROR: Build failed"
    exit 1
fi
