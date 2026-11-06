import os, gzip, zlib, struct, io, sys, time

DST = os.path.join(os.path.dirname(__file__), 'uramdisk.image.gz')
BB  = os.path.join(os.path.dirname(__file__), 'uramdisk_src', 'busybox-armv7')

if not os.path.exists(BB):
    sys.exit('busybox binary missing: ' + BB)
bb = open(BB, 'rb').read()
print('busybox: %d bytes' % len(bb))

INIT = (
    "#!/bin/sh\n"
    "mount -t proc none /proc\n"
    "mount -t sysfs none /sys\n"
    "mount -t devtmpfs none /dev 2>/dev/null || mount -t tmpfs none /dev\n"
    "hostname t9dev\n"
    "echo\n"
    "echo '=============================================='\n"
    "echo ' T9+ devboard: trampoline initramfs active'\n"
    "echo '=============================================='\n"
    "echo 'Waiting for microSD Partition 2 (/dev/mmcblk0p2)...'\n"
    "for i in 1 2 3 4 5 6 7 8 9 10; do\n"
    "  if [ -b /dev/mmcblk0p2 ]; then break; fi\n"
    "  sleep 0.5\n"
    "done\n"
    "\n"
    "if [ -b /dev/mmcblk0p2 ]; then\n"
    "  echo 'Mounting /dev/mmcblk0p2 to /new_root...'\n"
    "  mkdir -p /new_root\n"
    "  if mount -t ext4 /dev/mmcblk0p2 /new_root; then\n"
    "    mkdir -p /new_root/proc /new_root/sys /new_root/dev\n"
    "    if [ -e /new_root/usr/lib/systemd/systemd ] || [ -e /new_root/lib/systemd/systemd ]; then\n"
    "      INITARG=/sbin/init\n"
    "    else\n"
    "      INITARG=/bin/sh\n"
    "      echo 'note: no systemd in rootfs; falling back to rootfs shell'\n"
    "    fi\n"
    "    mount --move /proc /new_root/proc\n"
    "    mount --move /sys /new_root/sys\n"
    "    mount --move /dev /new_root/dev\n"
    "    if [ -s /new_root/etc/hostname ]; then\n"
    "      hostname \"$(cat /new_root/etc/hostname)\"\n"
    "    fi\n"
    "    echo \"Switching root to PYNQ rootfs ($INITARG)...\"\n"
    "    exec /sbin/switch_root /new_root $INITARG\n"
    "    echo 'ERROR: switch_root exec failed, dropping to rescue shell'\n"
    "  else\n"
    "    echo 'ERROR: Failed to mount /dev/mmcblk0p2 as ext4'\n"
    "  fi\n"
    "else\n"
    "  echo 'ERROR: /dev/mmcblk0p2 block device did not appear'\n"
    "fi\n"
    "echo '=============================================='\n"
    "echo ' Dropping to recovery shell'\n"
    "echo ' try: uname -a ; ls -l /dev/mmc* ; mount'\n"
    "echo '=============================================='\n"
    "while :; do setsid cttyhack /bin/sh </dev/console >/dev/console 2>&1; echo 'shell exited, restarting'; sleep 1; done\n"
)

def pad4(n):
    return (4 - (n % 4)) % 4

def name_area(name_len):
    # Kernel N_ALIGN(name_len) = ((name_len + 1) & ~3) + 2, where name_len
    # includes the NUL. Gen_init_cpio writes the same: name + pad so that
    # (110 + name_area) % 4 == 0 (110 is 2 mod 4).
    return (((name_len + 1) & ~3) + 2)

def newc_entry(ino, name, mode, data=b'', nlink=1, dev=(0, 0)):
    name_b = name.encode()
    nsz = len(name_b) + 1
    return ('070701'
            + format(ino, '08X')
            + format(mode, '08X')
            + '00000000'       # uid
            + '00000000'       # gid
            + format(nlink, '08X')
            + '00000000'       # mtime
            + format(len(data), '08X')   # filesize
            + '00000000'       # dev maj
            + '00000000'       # dev min
            + format(dev[0], '08X')      # rmaj (char/block nodes)
            + format(dev[1], '08X')      # rmin
            + format(nsz, '08X')
            + '00000000').encode() \
        + name_b + b'\0' + b'\0' * (name_area(nsz) - nsz) \
        + data + b'\0' * pad4(len(data))

out = io.BytesIO()
ino = 100

def d(name):
    global ino
    ino += 1
    out.write(newc_entry(ino, name, 0o040755, b'', nlink=2))

def f(name, data):
    global ino
    ino += 1
    out.write(newc_entry(ino, name, 0o100755, data))

def s(name, target):
    global ino
    ino += 1
    out.write(newc_entry(ino, name, 0o120777, target.encode() + b'\0'))

def c_dev(name, maj, minr):
    global ino
    ino += 1
    out.write(newc_entry(ino, name, 0o020600, b'', dev=(maj, minr)))

d('.')
d('dev'); d('proc'); d('sys'); d('bin'); d('sbin')
c_dev('dev/console', 5, 1)
c_dev('dev/null', 1, 3)
c_dev('dev/zero', 1, 5)
c_dev('dev/tty', 5, 0)
d('etc'); d('root'); d('tmp'); d('var'); d('usr')
d('usr/bin'); d('usr/sbin'); d('mnt')
f('bin/busybox', bb)
for cmd in ['sh', 'ash', 'ls', 'cat', 'mount', 'umount', 'ps', 'kill',
            'mkdir', 'rmdir', 'rm', 'cp', 'mv', 'ln', 'echo', 'uname',
            'sync', 'dd', 'lsmod', 'insmod', 'ifconfig', 'sleep', 'head',
            'tail', 'grep', 'dmesg', 'fdisk', 'hostname', 'setsid',
            'cttyhack', 'sed', 'awk', 'vi', 'wget', 'reboot', 'md5sum',
            'sha256sum', 'free', 'df', 'cmp']:
    s('bin/' + cmd, 'busybox')
s('sbin/switch_root', '/bin/busybox')
f('init', INIT.encode())
out.write(newc_entry(0, 'TRAILER!!!', 0o000000, b''))
out.write(b'\0' * 512)

cpio = out.getvalue()
gz = gzip.compress(cpio, 9, mtime=int(time.time()))
open(DST + '.gz-only.tmp', 'wb').write(gz)

# wrap in uImage (legacy) header: os=Linux(5), arch=ARM(2), type=RAMDisk(3), comp=gzip(1)
hdr = bytearray(64)
struct.pack_into('>I', hdr, 0, 0x27051956)   # magic
struct.pack_into('>I', hdr, 8,  int(time.time()))
struct.pack_into('>I', hdr, 12, len(gz))
struct.pack_into('>I', hdr, 16, 0x02000000)  # ih_load: already loaded at 0x02000000 by fatload
struct.pack_into('>I', hdr, 24, zlib.crc32(gz) & 0xFFFFFFFF)
hdr[28] = 5   # os = linux
hdr[29] = 2   # arch = arm
hdr[30] = 3   # type = ramdisk
hdr[31] = 1   # comp = gzip
name = b'busybox initrd t9 devboard'
hdr[32:32 + len(name)] = name
struct.pack_into('>I', hdr, 4, zlib.crc32(bytes(hdr)) & 0xFFFFFFFF)

fimg = bytes(hdr) + gz
open(DST, 'wb').write(fimg)
print('cpio: %d bytes, gzip: %d bytes' % (len(cpio), len(gz)))
print('uramdisk.image.gz: %d bytes -> %s' % (len(fimg), DST))
print('sha256: %s' % zlib.crc32(fimg))
import hashlib
print(hashlib.sha256(fimg).hexdigest())

# --- verify the cpio exactly as init/ramfs.c parses it ---
def nalign(l):                      # kernel N_ALIGN
    return (((l + 1) & ~3) + 2)

dec = gzip.decompress(gz)
off, recs, names = 0, 0, []
in_trailer = False
while not in_trailer:
    while off < len(dec) and dec[off] == 0:     # do_reset: eat zeros
        off += 1
    if off >= len(dec):
        sys.exit('VERIFY FAIL: archive ends with no TRAILER!!!')
    if off & 3:
        sys.exit('VERIFY FAIL: record misaligned at offset %d' % off)
    if dec[off:off + 6] not in (b'070701', b'070702'):
        sys.exit('VERIFY FAIL: junk at record start %d: %r' % (off, dec[off:off + 12]))
    fields = [int(dec[off + 6 + 8 * k:off + 14 + 8 * k], 16) for k in range(13)]
    body_len, namesize = fields[6], fields[11]
    name = dec[off + 110:off + 110 + namesize - 1].decode()
    data_ofs = off + 110 + nalign(namesize)
    recs += 1
    names.append(name)
    if name == 'TRAILER!!!':
        in_trailer = True
        trailer_at = off
    off = data_ofs + body_len
    if off > len(dec):
        sys.exit('VERIFY FAIL: truncated after %r (%d > %d)' % (name, off, len(dec)))
while off < len(dec) and dec[off] == 0:
    off += 1
if off != len(dec):
    sys.exit('VERIFY FAIL: junk after trailer at %d' % off)
if 'init' not in names:
    sys.exit('VERIFY FAIL: no /init in archive')
print('cpio verify OK: %d records (trailer at %d of %d bytes), /init present' % (recs, trailer_at or -1, len(dec)))
