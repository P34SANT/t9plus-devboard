import mmap, os, struct, time

fd = os.open('/dev/mem', os.O_RDWR | os.O_SYNC)
mem = mmap.mmap(fd, 4096, offset=0xE000A000)

def reg_r(off):
    return struct.unpack('<I', mem[off:off+4])[0]

def reg_w(off, val):
    mem[off:off+4] = struct.pack('<I', val)

PIN_SWDIO = 1 # F20, FAN3 Pin 3
PIN_NRST  = 2 # J20, FAN4 Pin 3

# Set both SWDIO and nRST as inputs
reg_w(0x0284, reg_r(0x0284) & ~((1 << PIN_SWDIO) | (1 << PIN_NRST)))
reg_w(0x0288, reg_r(0x0288) & ~((1 << PIN_SWDIO) | (1 << PIN_NRST)))

print("Monitoring FAN3 Pin 3 (SWDIO, F20) and FAN4 Pin 3 (nRST, J20) for 10 seconds...")
print("If connected to STM32, let's see their values:")

for i in range(20):
    data = reg_r(0x0068)
    swdio = (data >> PIN_SWDIO) & 1
    nrst  = (data >> PIN_NRST) & 1
    print("t=%4.1fs: SWDIO(F20) = %d,  nRST(J20) = %d" % (i * 0.5, swdio, nrst))
    time.sleep(0.5)
