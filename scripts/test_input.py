import mmap, os, struct, time

fd = os.open('/dev/mem', os.O_RDWR | os.O_SYNC)
mem = mmap.mmap(fd, 4096, offset=0xE000A000)

def reg_r(off):
    return struct.unpack('<I', mem[off:off+4])[0]

def reg_w(off, val):
    mem[off:off+4] = struct.pack('<I', val)

PIN_SWDIO = 1
PIN_SWCLK = 0
PIN_NRST = 2

# Set SWDIO to IN
reg_w(0x0284, reg_r(0x0284) & ~(1 << PIN_SWDIO))
reg_w(0x0288, reg_r(0x0288) & ~(1 << PIN_SWDIO))

print("SWDIO set to INPUT.")
for i in range(5):
    val = (reg_r(0x0068) >> PIN_SWDIO) & 1
    print("SWDIO read %d: %d" % (i, val))
    time.sleep(0.1)

# Now pulse SWCLK 10 times and read SWDIO
reg_w(0x0284, reg_r(0x0284) | (1 << PIN_SWCLK))
reg_w(0x0288, reg_r(0x0288) | (1 << PIN_SWCLK))

mask_clk = (~(1 << PIN_SWCLK)) & 0xFFFF
print("Toggling SWCLK with SWDIO as input:")
for i in range(5):
    reg_w(0x0010, (mask_clk << 16) | 0) # clk low
    time.sleep(0.01)
    val0 = (reg_r(0x0068) >> PIN_SWDIO) & 1
    reg_w(0x0010, (mask_clk << 16) | (1 << PIN_SWCLK)) # clk high
    time.sleep(0.01)
    val1 = (reg_r(0x0068) >> PIN_SWDIO) & 1
    print("Cycle %d: CLK=0 dio=%d, CLK=1 dio=%d" % (i, val0, val1))
