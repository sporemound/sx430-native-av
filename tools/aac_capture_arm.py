"""Small ARMv5 one-shot and multi-batch AAC capture wrapper."""
import struct

CAPACITY = 16384
ALLOCATION = 18432
CONTROL = 1024
PAYLOAD = 1280
ORIGINAL = 0xff077fd0
SLOT = 0xbf80
MAGIC = 0x31434141

class Asm:
    def __init__(self):
        self.words = []
        self.labels = {}
        self.fixups = []

    def w(self, v):
        self.words.append(v)

    def label(self, n):
        self.labels[n] = len(self.words) * 4

    def branch(self, n, cond=14):
        self.fixups.append((len(self.words), n, 'b', cond))
        self.w(0)

    def literal(self, rd, n):
        self.fixups.append((len(self.words), n, 'ldr', rd))
        self.w(0)

    def imm(self, v):
        for r in range(16):
            x = ((v << (2 * r)) | (v >> (32 - 2 * r if r else 32))) & 0xffffffff
            if x < 256:
                return (r << 8) | x
        raise ValueError(hex(v))

    def dp(self, op, rd, rn, x, imm=True, s=False):
        self.w(0xe0000000 | (int(imm) << 25) | (op << 21) | (int(s) << 20) | (rn << 16) | (rd << 12) | (self.imm(x) if imm else x))

    def mov(self, rd, n):
        self.dp(13, rd, 0, n)

    def cmp(self, r, n, imm=True):
        self.dp(10, 0, r, n, imm, True)

    def ldr(self, rd, rn, off=0):
        self.w(0xe5900000 | (rn << 16) | (rd << 12) | off)

    def st(self, rd, rn, off=0):
        self.w(0xe5800000 | (rn << 16) | (rd << 12) | off)

    def range(self):
        self.dp(14, 8, 6, 0x40000000)
        self.cmp(8, 0x1000)
        self.branch('refused', 3)
        self.dp(4, 9, 8, 7, False, True)
        self.branch('refused', 2)
        self.cmp(9, 0x10000000)
        self.branch('refused', 8)

    def finish(self):
        for i, n, kind, c in self.fixups:
            d = self.labels[n] - (i * 4 + 8)
            if kind == 'b':
                self.words[i] = (c << 28) | 0x0a000000 | ((d // 4) & 0xffffff)
            else:
                assert 0 <= d < 4096
                self.words[i] = 0xe59f0000 | (c << 12) | d
        return struct.pack('<' + 'I' * len(self.words), *self.words)
