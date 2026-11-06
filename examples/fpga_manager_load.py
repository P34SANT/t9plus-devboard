#!/usr/bin/env python3
"""
T9+ Safe Bitstream Loader (Linux FPGA Manager)
Swabs Vivado .bit files and loads them into XC7Z010 PL via Linux fpga_manager.
Avoids PCAP controller locking associated with generic PYNQ Overlay() on Z7010.
"""
import os
import sys
import subprocess

def load_bitstream(bitfile_path):
    if not os.path.isfile(bitfile_path):
        print(f"ERROR: Bitfile not found at {bitfile_path}")
        return False

    basename = os.path.splitext(os.path.basename(bitfile_path))[0]
    swapped_path = f"/tmp/{basename}_swapped.bin"

    print(f"==> Swapping endianness for {bitfile_path}...")
    with open(bitfile_path, "rb") as fin, open(swapped_path, "wb") as fout:
        while chunk := fin.read(65536):
            # Swab 16-bit words
            if len(chunk) % 2 != 0:
                chunk += b'\x00'
            swapped = bytearray(chunk)
            for i in range(0, len(swapped), 2):
                swapped[i], swapped[i+1] = swapped[i+1], swapped[i]
            fout.write(swapped)

    print("==> Installing to /lib/firmware/...")
    os.makedirs("/lib/firmware", exist_ok=True)
    fw_name = f"{basename}_swapped.bin"
    subprocess.run(["sudo", "cp", swapped_path, f"/lib/firmware/{fw_name}"], check=True)

    print("==> Streaming to /sys/class/fpga_manager/fpga0/firmware...")
    cmd = f'echo "{fw_name}" | sudo tee /sys/class/fpga_manager/fpga0/firmware'
    res = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL)

    if res.returncode == 0:
        print("==> SUCCESS: FPGA programmed! Check D1 green FPGA_DONE LED.")
        os.remove(swapped_path)
        return True
    else:
        print("==> ERROR: Programming failed.")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 fpga_manager_load.py <path_to_bitstream.bit>")
        sys.exit(1)
    load_bitstream(sys.argv[1])
