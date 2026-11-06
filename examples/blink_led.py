#!/usr/bin/env python3
"""
T9+ User LED Blink Example (PYNQ 3.0.1)
Controls onboard PL LEDs:
- D5 Red   (Pin M19, Bank 35)
- D6 Green (Pin M17, Bank 35)

Using PYNQ MMIO to access an AXI GPIO IP at base address 0x41200000.
"""
import time
import sys

try:
    from pynq import MMIO
except ImportError:
    print("ERROR: pynq library not found. Run this script inside PYNQ on the T9+ board.")
    sys.exit(1)

# Base address from Vivado Address Editor for AXI GPIO
AXI_GPIO_BASE = 0x41200000
ADDRESS_RANGE = 0x1000

GPIO_DATA = 0x0000  # Channel 1 Data Register
GPIO_TRI  = 0x0004  # Channel 1 Tri-state Register (0=output, 1=input)

def main():
    print("=" * 50)
    print(" Antminer T9+ LED Blink Test (D5 Red / D6 Green)")
    print("=" * 50)
    print(f"Connecting to AXI GPIO at 0x{AXI_GPIO_BASE:08X}...")

    gpio = MMIO(AXI_GPIO_BASE, ADDRESS_RANGE)

    # Set both LED pins as outputs
    gpio.write(GPIO_TRI, 0x00000000)
    print("GPIO Tri-state configured: All outputs.")
    print("Blinking... Press Ctrl+C to stop.")

    try:
        count = 0
        while True:
            # Alternating pattern
            if count % 2 == 0:
                gpio.write(GPIO_DATA, 0x01)  # D5 Red ON, D6 Green OFF
                print("LED State: [ D5 RED ON  ] [ D6 GREEN OFF ]")
            else:
                gpio.write(GPIO_DATA, 0x02)  # D5 Red OFF, D6 Green ON
                print("LED State: [ D5 RED OFF ] [ D6 GREEN ON  ]")
            time.sleep(0.5)
            count += 1
    except KeyboardInterrupt:
        gpio.write(GPIO_DATA, 0x00)  # All OFF
        print("\nTest completed. LEDs turned off.")

if __name__ == "__main__":
    main()
