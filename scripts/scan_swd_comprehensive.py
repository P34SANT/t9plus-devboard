import mmap, os, struct, time

fd = os.open('/dev/mem', os.O_RDWR | os.O_SYNC)
mem = mmap.mmap(fd, 4096, offset=0xE000A000)

def reg_r(off):
    return struct.unpack('<I', mem[off:off+4])[0]

def reg_w(off, val):
    mem[off:off+4] = struct.pack('<I', val)

PIN_SWCLK = 0
PIN_SWDIO = 1
PIN_NRST  = 2

def set_clk(val):
    mask = (~(1 << PIN_SWCLK)) & 0xFFFF
    reg_w(0x0010, (mask << 16) | ((1 if val else 0) << PIN_SWCLK))

def set_dio(val):
    mask = (~(1 << PIN_SWDIO)) & 0xFFFF
    reg_w(0x0010, (mask << 16) | ((1 if val else 0) << PIN_SWDIO))

def get_dio():
    return (reg_r(0x0068) >> PIN_SWDIO) & 1

def dio_out():
    reg_w(0x0284, reg_r(0x0284) | (1 << PIN_SWDIO))
    reg_w(0x0288, reg_r(0x0288) | (1 << PIN_SWDIO))

def dio_in():
    reg_w(0x0284, reg_r(0x0284) & ~(1 << PIN_SWDIO))
    reg_w(0x0288, reg_r(0x0288) & ~(1 << PIN_SWDIO))

def assert_reset(val):
    if val: # Assert reset (drive low)
        reg_w(0x0284, reg_r(0x0284) | (1 << PIN_NRST))
        reg_w(0x0288, reg_r(0x0288) | (1 << PIN_NRST))
        mask = (~(1 << PIN_NRST)) & 0xFFFF
        reg_w(0x0010, (mask << 16) | 0)
    else: # Release reset (tri-state, pulled high externally)
        reg_w(0x0284, reg_r(0x0284) & ~(1 << PIN_NRST))
        reg_w(0x0288, reg_r(0x0288) & ~(1 << PIN_NRST))

# Initialize CLK as output
reg_w(0x0284, reg_r(0x0284) | (1 << PIN_SWCLK))
reg_w(0x0288, reg_r(0x0288) | (1 << PIN_SWCLK))
set_clk(1)
dio_out()
set_dio(1)
assert_reset(False)
time.sleep(0.05)

def clk_delay(us):
    if us > 0:
        time.sleep(us / 1000000.0)
    else:
        for _ in range(20): pass

def write_bit(b, delay_us):
    set_dio(b)
    set_clk(0)
    clk_delay(delay_us)
    set_clk(1)
    clk_delay(delay_us)

def read_bit(delay_us):
    set_clk(0)
    clk_delay(delay_us)
    b = get_dio()
    set_clk(1)
    clk_delay(delay_us)
    return b

def try_swd_connect(delay_us=5, reset_first=False):
    if reset_first:
        assert_reset(True)
        time.sleep(0.02)
        assert_reset(False)
        time.sleep(0.05)

    dio_out()
    # Line reset: >50 cycles high
    for _ in range(60):
        write_bit(1, delay_us)

    # JTAG-to-SWD switch sequence: 0xE79E (LSB first: 0111 1001 1110 0111)
    seq = 0xE79E
    for _ in range(16):
        write_bit(seq & 1, delay_us)
        seq >>= 1

    # Line reset: >50 cycles high
    for _ in range(60):
        write_bit(1, delay_us)

    # Idle cycles: 8 low
    for _ in range(8):
        write_bit(0, delay_us)

    # Request DPIDR read (packet request 0xA5 = 10100101b, LSB first)
    # Start(1), APnDP=0 (DP), RnW=1 (Read), A[2:3]=00, Parity=1, Stop=0, Park=1
    req = 0xA5
    for _ in range(8):
        write_bit(req & 1, delay_us)
        req >>= 1

    # Turnaround
    dio_in()
    # 1 cycle turnaround
    set_clk(0)
    clk_delay(delay_us)
    set_clk(1)
    clk_delay(delay_us)

    # Read 3-bit ACK (LSB first)
    ack = 0
    for i in range(3):
        ack |= (read_bit(delay_us) << i)

    dpidr = 0
    parity = 0
    if ack == 1: # OK
        for i in range(32):
            b = read_bit(delay_us)
            dpidr |= (b << i)
            parity ^= b
        p_bit = read_bit(delay_us)

    # Turnaround back to host
    set_clk(0)
    clk_delay(delay_us)
    set_clk(1)
    clk_delay(delay_us)
    dio_out()
    for _ in range(8):
        write_bit(0, delay_us)

    return ack, dpidr

print("--- Testing SWD Communication ---")
for delay in [10, 5, 2, 0]:
    ack, dpidr = try_swd_connect(delay_us=delay, reset_first=False)
    print("Delay %2d us: ACK=%d (binary 0b%03s), DPIDR=0x%08X" % (delay, ack, bin(ack)[2:], dpidr))
    if ack == 1:
        print(">>> SUCCESS! Found Cortex DPIDR: 0x%08X <<<" % dpidr)
        break

if ack != 1:
    print("\n--- Trying with Target Reset Pulse ---")
    for delay in [10, 5, 2, 0]:
        ack, dpidr = try_swd_connect(delay_us=delay, reset_first=True)
        print("Reset test Delay %2d us: ACK=%d, DPIDR=0x%08X" % (delay, ack, dpidr))
        if ack == 1:
            print(">>> SUCCESS with reset! DPIDR: 0x%08X <<<" % dpidr)
            break
