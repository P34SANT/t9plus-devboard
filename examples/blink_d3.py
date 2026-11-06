#!/usr/bin/env python3
"""
Blink Onboard Bicolor LED D3 (PS MIO GPIO)
- D3 Red:   MIO37 -> Linux GPIO 549 (base 512 + 37)
- D3 Green: MIO38 -> Linux GPIO 550 (base 512 + 38)

No FPGA bitstream required! (Driven by Zynq PS GPIO controller)
Run with: sudo python3 blink_d3.py
"""
import time
import os
import sys

RED_GPIO = 549    # MIO 37
GREEN_GPIO = 550  # MIO 38

def setup_pin(pin):
    path = f"/sys/class/gpio/gpio{pin}"
    if not os.path.exists(path):
        with open("/sys/class/gpio/export", "w") as f:
            f.write(str(pin))
    with open(f"{path}/direction", "w") as f:
        f.write("out")

def write_pin(pin, val):
    with open(f"/sys/class/gpio/gpio{pin}/value", "w") as f:
        f.write(str(val))

def main():
    print("==================================================")
    print(" Antminer T9+ LED D3 Bicolor Blink Test (PS GPIO)")
    print("==================================================")
    print("Setting up MIO37 (Red) and MIO38 (Green)...")
    setup_pin(RED_GPIO)
    setup_pin(GREEN_GPIO)

    print("Blinking D3 alternating RED <-> GREEN (Ctrl+C to stop)...")
    try:
        for i in range(15):
            # RED ON, GREEN OFF
            write_pin(RED_GPIO, 1)
            write_pin(GREEN_GPIO, 0)
            print(f"Cycle {i+1:02d}/15: [ D3 RED ]", end="\r", flush=True)
            time.sleep(0.4)

            # RED OFF, GREEN ON
            write_pin(RED_GPIO, 0)
            write_pin(GREEN_GPIO, 1)
            print(f"Cycle {i+1:02d}/15: [ D3 GREEN ]", end="\r", flush=True)
            time.sleep(0.4)

        # Turn both off at the end
        write_pin(RED_GPIO, 0)
        write_pin(GREEN_GPIO, 0)
        print("\nTest completed successfully. Both turned off.")
    except KeyboardInterrupt:
        write_pin(RED_GPIO, 0)
        write_pin(GREEN_GPIO, 0)
        print("\nInterrupted. LEDs turned off.")

if __name__ == "__main__":
    main()
