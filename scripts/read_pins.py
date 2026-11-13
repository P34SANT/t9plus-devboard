import mmap, os, struct

fd = os.open('/dev/mem', os.O_RDWR | os.O_SYNC)
mem = mmap.mmap(fd, 4096, offset=0xE000A000)

data_ro = struct.unpack('<I', mem[0x0068:0x006C])[0]
dirm = struct.unpack('<I', mem[0x0284:0x0288])[0]
oen = struct.unpack('<I', mem[0x0288:0x028C])[0]

print("DATA_2_RO: 0x%04X" % data_ro)
print("DIRM_2:    0x%04X" % dirm)
print("OEN_2:     0x%04X" % oen)

pin_names = {
    0: "SWCLK (J18)",
    1: "SWDIO (F20, FAN3 P3)",
    2: "nRST  (J20, FAN4 P3)",
    3: "BOOT0",
}

for pin in range(16):
    val = (data_ro >> pin) & 1
    direction = "OUT" if ((dirm >> pin) & 1) else "IN"
    name = pin_names.get(pin, "IO%d" % pin)
    print("EMIO %2d [%-20s]: %d (%s)" % (pin, name, val, direction))
