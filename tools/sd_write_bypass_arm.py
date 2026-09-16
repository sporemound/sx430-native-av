"""SX430 100b SD write bypass proxy for continuous native H.264 streaming.

Decouples DIGIC 4+ hardware video encoder from task_MovieWriter and task_FileWrite.
Intercepts the descriptor enqueue call at 0xff1ecce8 in task_MovieRecord (0xff1ec9c0),
records the hardware encoder ring descriptor into an in-RAM transmission ring, and returns
success (r0=0) immediately without dispatching disk I/O.
"""
import hashlib
from pathlib import Path
import struct
import sys

# Locate root work or tools dir if needed
for p in [Path(__file__).resolve().parent] + list(Path(__file__).resolve().parents):
    if (p / 'work' / 'aac_capture_arm.py').exists():
        sys.path.insert(0, str(p / 'work'))
        break
    elif (p / 'tools' / 'aac_capture_arm.py').exists():
        sys.path.insert(0, str(p / 'tools'))
        break
    elif (p / 'aac_capture_arm.py').exists():
        sys.path.insert(0, str(p))
        break

from aac_capture_arm import Asm

ORIGINAL = 0xff1ec9c0
END = 0xff1ecdbc
WRITER = 0xff37d5e0
SLOT = 0x7c70

BODY = 256
PROXY = 2048
CONTROL = 4096
DESCRIPTORS = 4352
CAPACITY = 262144
ALLOCATION = 8192
MAGIC = 0x42505359  # 'YSBP'
RING_CAPACITY = 32

ROOT = Path(r"C:\Users\alexw\Documents\Codex\2026-09-14\files-pasted-by-the-user-canon")

def rom_bytes():
    rom_file = ROOT / 'outputs/camera-evidence/dump-attempt-002/PRIMARY.BIN'
    if not rom_file.exists():
        for p in [Path(__file__).resolve().parent] + list(Path(__file__).resolve().parents):
            cand = p / 'outputs/camera-evidence/dump-attempt-002/PRIMARY.BIN'
            if cand.exists():
                rom_file = cand
                break
    data = rom_file.read_bytes()
    assert hashlib.sha256(data).hexdigest() == 'a67792b34e74a35ff93d7362e9bd1b6e2e3196cee471074d03e0a8fca1de031b'
    return data

def word(rom, addr):
    return struct.unpack_from('<I', rom, addr - 0xff010000)[0]

def branch(src, dst, cond=14, link=False):
    delta = dst - src - 8
    if delta % 4 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError(f'Branch range overflow: delta={delta}')
    return (cond << 28) | 0x0a000000 | (int(link) << 24) | ((delta // 4) & 0xffffff)

def entry(base):
    a = Asm()
    a.w(0xe92d5fff)  # push {r0-r12, lr}
    a.w(0xe10fc000)  # mrs r12, cpsr
    a.w(0xe92d5000)  # push {r12, lr}
    a.literal(4, 'slot')
    a.ldr(5, 4)
    a.literal(6, 'self')
    a.cmp(5, 6, False)
    a.branch('foreign', 1)  # if slot != self, branch foreign

    # Check mode: if one-shot (bit 0 == 0), detach by restoring ORIGINAL to SLOT. If continuous (bit 0 == 1), keep installed.
    a.literal(5, 'control')
    a.ldr(6, 5, 8)   # mode flags at control + 8
    a.dp(0, 7, 6, 1) # tst r6, #1
    a.cmp(7, 0)
    a.branch('keep', 1) # if bit 0 != 0, keep installed
    a.literal(7, 'original')
    a.st(7, 4)       # detach for one-shot mode

    a.label('keep')
    a.w(0xe8bd5000)  # pop {r12, lr}
    a.w(0xe128f00c)  # msr cpsr_f, r12
    a.w(0xe8bd5fff)  # pop {r0-r12, lr}
    a.literal(15, 'body')

    a.label('foreign')
    a.w(0xe8bd5000)
    a.w(0xe128f00c)
    a.w(0xe8bd5fff)
    a.literal(15, 'original')

    for n, v in [('slot', SLOT), ('self', base), ('original', ORIGINAL),
                 ('control', base + CONTROL), ('body', base + BODY)]:
        a.label(n)
        a.w(v)

    data = a.finish()
    assert len(data) <= BODY
    return data

def bypass_proxy(base):
    a = Asm()
    a.w(0xe92d5fff)  # push {r0-r12, lr}
    a.w(0xe10fc000)  # mrs r12, cpsr
    a.w(0xe92d5000)  # push {r12, lr}

    a.literal(4, 'control')
    a.ldr(5, 4, 4)   # state flag at control+4 (1 = bypass active, 0 = disabled)
    a.cmp(5, 0)
    a.branch('tail', 0)  # if disabled (r5 == 0), branch tail (cond=0 EQ)

    # Validate length: r1 in [4, CAPACITY]
    a.cmp(1, 4)
    a.branch('refused', 3)  # blo refused (cond=3 CC/LO)
    a.literal(6, 'capacity')
    a.cmp(1, 6, False)
    a.branch('refused', 8)  # bhi refused (cond=8 HI)

    # Validate source pointer: r0 in [0x40000000, 0x50000000)
    a.cmp(0, 0x40000000)
    a.branch('refused', 3)  # blo refused (cond=3 CC/LO)
    a.literal(6, 'ram_end')
    a.cmp(0, 6, False)
    a.branch('refused', 2)  # bhs refused (cond=2 CS/HS)

    # Load ring write index & capacity
    a.ldr(6, 4, 28)  # write_index at control + 0x1c
    a.ldr(7, 4, 36)  # ring_capacity at control + 0x24
    a.cmp(7, 0)
    a.branch('refused', 0)  # beq refused (cond=0 EQ)

    # Calculate descriptor entry address = control + 256 + (write_index << 5)
    a.dp(4, 8, 4, 256)           # add r8, r4, #256
    a.w(0xe0888286)              # add r8, r8, r6, lsl #5

    # Write descriptor fields (32 bytes):
    # +0x00: Status = 1 (Ready)
    a.mov(9, 1)
    a.st(9, 8, 0)

    # +0x04: Sequence = total_frames (control + 0x14)
    a.ldr(9, 4, 20)
    a.st(9, 8, 4)

    # +0x08: Source address (r0)
    a.st(0, 8, 8)

    # +0x0C: Payload length (r1)
    a.st(1, 8, 12)

    # +0x10: NAL type / flags from caller stack [sp + 64 + 0x44]
    a.ldr(9, 13, 64 + 0x44)
    a.st(9, 8, 16)

    # +0x14: Timestamp from caller stack [sp + 64 + 0x40]
    a.ldr(9, 13, 64 + 0x40)
    a.st(9, 8, 20)

    # +0x18: Prefix / flags
    a.mov(9, 0)
    a.st(9, 8, 24)

    # +0x1C: Reserved
    a.st(9, 8, 28)

    # Update latest summary in CONTROL
    a.st(0, 4, 48)   # last_source at control + 0x30
    a.st(1, 4, 52)   # last_length at control + 0x34
    a.ldr(9, 13, 64 + 0x44)
    a.st(9, 4, 44)   # last_nal_type at control + 0x2c
    a.ldr(9, 13, 64 + 0x40)
    a.st(9, 4, 40)   # last_pts at control + 0x28

    # Increment total_frames at control + 0x14
    a.ldr(9, 4, 20)
    a.dp(4, 9, 9, 1) # add r9, r9, #1
    a.st(9, 4, 20)

    # Advance write_index = (write_index + 1) % capacity
    a.dp(4, 6, 6, 1)
    a.cmp(6, 7, False)
    a.w(0x03a06000)  # moveq r6, #0
    a.st(6, 4, 28)

    # Return success (r0 = 0) without calling stock WRITER
    a.w(0xe8bd5000)  # pop {r12, lr}
    a.w(0xe128f00c)  # msr cpsr_f, r12
    a.w(0xe8bd5fff)  # pop {r0-r12, lr}
    a.mov(0, 0)      # return r0 = 0
    a.w(0xe12fff1e)  # bx lr (return directly to MovieRecord caller!)

    a.label('refused')
    # Refusal path: increment refusal count at control + 0x38
    a.ldr(9, 4, 56)
    a.dp(4, 9, 9, 1)
    a.st(9, 4, 56)
    a.w(0xe8bd5000)
    a.w(0xe128f00c)
    a.w(0xe8bd5fff)
    a.mov(0, 0)
    a.w(0xe12fff1e)  # bx lr

    a.label('tail')
    # Pass-through fallback path
    a.w(0xe8bd5000)
    a.w(0xe128f00c)
    a.w(0xe8bd5fff)
    a.literal(15, 'writer')

    for n, v in [('control', base + CONTROL), ('capacity', CAPACITY),
                 ('ram_end', 0x50000000), ('writer', WRITER)]:
        a.label(n)
        a.w(v)

    data = a.finish()
    assert len(data) <= CONTROL - PROXY
    return data

def relocate(base, rom=None):
    rom = rom if rom is not None else rom_bytes()
    length = END - ORIGINAL
    words = [word(rom, a) for a in range(ORIGINAL, END, 4)]
    extra = []
    report = []

    def pool(v):
        address = base + BODY + length + len(extra) * 4
        extra.append(v)
        return address

    def veneer(target):
        address = pool(0xe51ff004)
        pool(target)
        return address

    for i, w in enumerate(list(words)):
        old = ORIGINAL + i * 4
        new = base + BODY + i * 4
        cond = w >> 28
        if cond == 15:
            raise ValueError('Unsupported unconditional encoding')

        if (w & 0x0e000000) == 0x0a000000:
            imm = w & 0xffffff
            if imm & 0x800000:
                imm -= 0x1000000
            target = (old + 8 + imm * 4) & 0xffffffff
            link = bool(w & 0x01000000)
            if old == 0xff1ecce8:
                # Replace call to WRITER (0xff37d5e0) with call to bypass proxy
                assert link and target == WRITER
                dst = base + PROXY
            elif ORIGINAL <= target < END:
                dst = base + BODY + target - ORIGINAL
            else:
                dst = veneer(target)
            words[i] = branch(new, dst, cond, link)
            report.append({'source': old, 'kind': 'branch', 'original_target': target, 'relocated_target': dst, 'link': link})
        elif (w & 0x0f7f0000) == 0x051f0000:
            target = old + 8 + ((w & 0xfff) if (w & 0x00800000) else -(w & 0xfff))
            value = word(rom, target)
            literal = pool(value)
            delta = literal - new - 8
            assert 0 <= delta < 4096
            words[i] = (w & 0xf000f000) | 0x059f0000 | delta
            report.append({'source': old, 'kind': 'literal', 'original_pointer': target, 'value': value})

    data = struct.pack('<' + 'I' * (len(words) + len(extra)), *(words + extra))
    assert BODY + len(data) <= PROXY
    return data, report

def build(base, continuous=True, ring_capacity=RING_CAPACITY):
    rom = rom_bytes()
    body, report = relocate(base, rom)
    result = bytearray(ALLOCATION)

    # 1. Entry trampoline at 0
    entry_code = entry(base)
    result[0:len(entry_code)] = entry_code

    # 2. Relocated MovieRecord body at BODY (256)
    result[BODY:BODY + len(body)] = body

    # 3. Bypass proxy at PROXY (2048)
    proxy_code = bypass_proxy(base)
    result[PROXY:PROXY + len(proxy_code)] = proxy_code

    # 4. Initialize CONTROL header at CONTROL (4096)
    header = struct.pack('<16I',
        MAGIC,
        1,  # Active
        1 if continuous else 0,
        SLOT,
        ORIGINAL,
        0,  # total_frames
        0,  # dropped_frames
        0,  # write_index
        0,  # read_index
        ring_capacity,
        0, 0, 0, 0, 0, 0  # stats / reserved
    )
    result[CONTROL:CONTROL + len(header)] = header

    return bytes(result), {
        'code_bytes': len(result),
        'relocations': len(report),
        'continuous': continuous,
        'ring_capacity': ring_capacity,
        'proxy_offset': PROXY,
        'control_offset': CONTROL,
        'descriptors_offset': DESCRIPTORS
    }

if __name__ == '__main__':
    data, rep = build(0x41000000)
    print('BUILD SUCCESS: code_bytes =', len(data), 'relocations =', rep['relocations'])
