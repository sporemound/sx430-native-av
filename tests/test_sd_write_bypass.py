"""Comprehensive unit tests for Step C1 SD write bypass proxy using Unicorn emulator."""
from pathlib import Path
import struct
import sys
import unittest

# Multi-level search path setup for emulator & disassembler dependencies
for p in [Path(__file__).resolve().parent] + list(Path(__file__).resolve().parents):
    if (p / 'work' / 'emulator-deps').exists():
        sys.path.insert(0, str(p / 'work'))
        sys.path.insert(0, str(p / 'work/emulator-deps'))
        sys.path.insert(0, str(p / 'work/disasm-deps'))
        break
    elif (p / 'emulator-deps').exists():
        sys.path.insert(0, str(p))
        sys.path.insert(0, str(p / 'emulator-deps'))
        sys.path.insert(0, str(p / 'disasm-deps'))
        break

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from capstone.arm import ARM_OP_REG, ARM_OP_MEM, ARM_REG_PC

# Import sd_write_bypass_arm
try:
    from sd_write_bypass_arm import *
except ImportError:
    for p in [Path(__file__).resolve().parent] + list(Path(__file__).resolve().parents):
        if (p / 'tools' / 'sd_write_bypass_arm.py').exists():
            sys.path.insert(0, str(p / 'tools'))
            break
        elif (p / 'work' / 'sd_write_bypass_arm.py').exists():
            sys.path.insert(0, str(p / 'work'))
            break
    from sd_write_bypass_arm import *

BASE = 0x41000000
RING = 0x48000000
STACK = 0x200000
DONE = 0x10000
MSG = 0x12000

REGS = [
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
    UC_ARM_REG_R12, UC_ARM_REG_LR
]

def put(u, p, v):
    u.mem_write(p, struct.pack('<I', v & 0xffffffff))

def get(u, p):
    return struct.unpack('<I', u.mem_read(p, 4))[0]

def machine(continuous=True):
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0, 0x800000)
    u.mem_map(0xff010000, 0xff0000)
    u.mem_write(0xff010000, rom_bytes())
    u.mem_map(BASE, 0x10000)
    u.mem_map(RING, 0x100000)

    code, _ = build(BASE, continuous=continuous)
    u.mem_write(BASE, code)

    u.reg_write(UC_ARM_REG_CPSR, 0xa0000013)
    u.reg_write(UC_ARM_REG_SP, STACK)
    for i, r in enumerate(REGS):
        u.reg_write(r, 0x333000 + i)
    u.reg_write(UC_ARM_REG_LR, DONE)

    put(u, SLOT, BASE)
    put(u, 0x7c0c, 4)  # movie_status = recording
    put(u, 0xd4d8, 3)
    put(u, 0xd5b0, RING)
    put(u, 0xd5b4, RING + 0x100000)

    return u

class SDBypassArmTests(unittest.TestCase):

    def test_all_pc_sensitive_instructions_relocated(self):
        md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        md.detail = True
        rom = rom_bytes()
        _, report = relocate(BASE, rom)
        seen = {r['source']: r for r in report}
        instructions = list(md.disasm(rom[ORIGINAL - 0xff010000 : END - 0xff010000], ORIGINAL))
        self.assertEqual(len(instructions), (END - ORIGINAL) // 4)

        for ins in instructions:
            pc = any((op.type == ARM_OP_REG and op.reg == ARM_REG_PC) or
                     (op.type == ARM_OP_MEM and (op.mem.base == ARM_REG_PC or op.mem.index == ARM_REG_PC))
                     for op in ins.operands)
            if pc and not ins.mnemonic.startswith('pop'):
                self.assertIn(ins.address, seen, ins.mnemonic + ' ' + ins.op_str)
            if ins.mnemonic.startswith('b') and not ins.mnemonic.startswith('bic'):
                self.assertIn(ins.address, seen)

    def test_bypass_proxy_intercepts_and_bypasses_sd_writer(self):
        u = machine(continuous=True)
        source_ptr = RING + 0x1000
        frame_len = 77368
        nal_type = 1
        pts = 45600

        put(u, STACK + 0x4c, source_ptr)
        put(u, STACK + 0x54, frame_len)
        put(u, STACK + 0x44, nal_type)
        put(u, STACK + 0x40, pts)

        u.reg_write(UC_ARM_REG_R0, source_ptr)
        u.reg_write(UC_ARM_REG_R1, frame_len)
        u.reg_write(UC_ARM_REG_LR, DONE)

        writer_hit = [False]
        def hook_writer(uc, address, size, user):
            if address == WRITER:
                writer_hit[0] = True
                uc.emu_stop()

        u.hook_add(UC_HOOK_CODE, hook_writer)
        u.emu_start(BASE + PROXY, DONE, count=10000)

        # 1. Verify WRITER was NOT called (SD write bypassed!)
        self.assertFalse(writer_hit[0], "Stock MovieWriter should be bypassed")

        # 2. Verify return code r0 == 0
        self.assertEqual(u.reg_read(UC_ARM_REG_R0), 0)

        # 3. Verify total frames incremented in control header
        self.assertEqual(get(u, BASE + CONTROL + 20), 1)  # total_frames = 1
        self.assertEqual(get(u, BASE + CONTROL + 28), 1)  # write_index = 1

        # 4. Verify ring descriptor table entry #0 (at DESCRIPTORS)
        desc_addr = BASE + DESCRIPTORS
        self.assertEqual(get(u, desc_addr + 0), 1)          # status = 1 (Ready)
        self.assertEqual(get(u, desc_addr + 4), 0)          # sequence = 0
        self.assertEqual(get(u, desc_addr + 8), source_ptr) # source address
        self.assertEqual(get(u, desc_addr + 12), frame_len) # length
        self.assertEqual(get(u, desc_addr + 16), nal_type)  # nal_type
        self.assertEqual(get(u, desc_addr + 20), pts)       # timestamp

    def test_multi_frame_continuous_ring_advance(self):
        u = machine(continuous=True)
        # Execute 5 successive frames
        for frame_idx in range(5):
            source_ptr = RING + 0x2000 * frame_idx
            frame_len = 10000 + frame_idx * 500
            nal_type = 5 if frame_idx == 0 else 1
            pts = 40000 + frame_idx * 3600

            put(u, STACK + 0x4c, source_ptr)
            put(u, STACK + 0x54, frame_len)
            put(u, STACK + 0x44, nal_type)
            put(u, STACK + 0x40, pts)

            u.reg_write(UC_ARM_REG_R0, source_ptr)
            u.reg_write(UC_ARM_REG_R1, frame_len)
            u.reg_write(UC_ARM_REG_LR, DONE)

            u.emu_start(BASE + PROXY, DONE, count=10000)

            self.assertEqual(u.reg_read(UC_ARM_REG_R0), 0)
            self.assertEqual(get(u, BASE + CONTROL + 20), frame_idx + 1)
            self.assertEqual(get(u, BASE + CONTROL + 28), (frame_idx + 1) % RING_CAPACITY)

            # Check individual descriptor entry
            desc_addr = BASE + DESCRIPTORS + frame_idx * 32
            self.assertEqual(get(u, desc_addr + 0), 1)
            self.assertEqual(get(u, desc_addr + 4), frame_idx)
            self.assertEqual(get(u, desc_addr + 8), source_ptr)
            self.assertEqual(get(u, desc_addr + 12), frame_len)
            self.assertEqual(get(u, desc_addr + 16), nal_type)
            self.assertEqual(get(u, desc_addr + 20), pts)

    def test_entry_trampoline_continuous_preserves_slot(self):
        u = machine(continuous=True)
        put(u, SLOT, BASE)
        before = [u.reg_read(r) for r in REGS]

        u.emu_start(BASE, BASE + BODY, count=1000)
        self.assertEqual(u.reg_read(UC_ARM_REG_PC), BASE + BODY)
        self.assertEqual([u.reg_read(r) for r in REGS], before)
        # In continuous mode, slot remains BASE
        self.assertEqual(get(u, SLOT), BASE)

    def test_entry_trampoline_oneshot_restores_slot(self):
        u = machine(continuous=False)
        put(u, SLOT, BASE)
        before = [u.reg_read(r) for r in REGS]

        u.emu_start(BASE, BASE + BODY, count=1000)
        self.assertEqual(u.reg_read(UC_ARM_REG_PC), BASE + BODY)
        self.assertEqual([u.reg_read(r) for r in REGS], before)
        # In one-shot mode, slot is restored to ORIGINAL
        self.assertEqual(get(u, SLOT), ORIGINAL)

    def test_bypass_proxy_disabled_pass_through_to_writer(self):
        u = machine(continuous=True)
        # Disable bypass (state = 0)
        put(u, BASE + CONTROL + 4, 0)

        source_ptr = RING + 0x1000
        frame_len = 77368
        u.reg_write(UC_ARM_REG_R0, source_ptr)
        u.reg_write(UC_ARM_REG_R1, frame_len)

        writer_hit = [False]
        def hook_writer(uc, address, size, user):
            if address == WRITER:
                writer_hit[0] = True
                uc.emu_stop()

        u.hook_add(UC_HOOK_CODE, hook_writer)
        u.emu_start(BASE + PROXY, WRITER + 4, count=10000)

        # When state = 0, should fall through to original WRITER
        self.assertTrue(writer_hit[0], "When disabled, proxy should pass through to WRITER")

    def test_bypass_proxy_refuses_out_of_bounds_and_increments_error_count(self):
        for bad_ptr, bad_len in [(RING, 2), (RING, CAPACITY + 100), (0x20000000, 1000), (0x60000000, 1000)]:
            with self.subTest(bad_ptr=bad_ptr, bad_len=bad_len):
                u = machine(continuous=True)
                put(u, STACK + 0x4c, bad_ptr)
                put(u, STACK + 0x54, bad_len)
                put(u, STACK + 0x44, 1)
                put(u, STACK + 0x40, 100)

                u.reg_write(UC_ARM_REG_R0, bad_ptr)
                u.reg_write(UC_ARM_REG_R1, bad_len)
                u.reg_write(UC_ARM_REG_LR, DONE)

                u.emu_start(BASE + PROXY, DONE, count=10000)
                self.assertEqual(u.reg_read(UC_ARM_REG_R0), 0)
                # Refusal error count at CONTROL + 0x38 incremented
                self.assertEqual(get(u, BASE + CONTROL + 56), 1)
                # Total valid frames not incremented
                self.assertEqual(get(u, BASE + CONTROL + 20), 0)

    def test_end_to_end_relocated_movierecord_callback(self):
        u = machine(continuous=True)
        u.reg_write(UC_ARM_REG_R0, MSG)
        put(u, SLOT, BASE)

        # Set up MovieRecord state block at 0x7bc0
        for off, v in [(8, 0), (0x4c, 4), (0x70, 3), (0x74, 3), (0x58, 25), (0x5c, 1000), (0x24, 1), (0x68, 1000)]:
            put(u, 0x7bc0 + off, v)

        calls = []
        _, report = relocate(BASE)
        external = {r['original_target'] for r in report if r['kind'] == 'branch' and not ORIGINAL <= r['original_target'] < END}

        pointer = RING + 64
        payload_len = 77368
        writer_called = [False]

        def hook(uc, address, size, user):
            if address == DONE:
                uc.emu_stop()
                return
            if address == WRITER:
                writer_called[0] = True
                uc.emu_stop()
                return
            if address not in external:
                return

            regs = [uc.reg_read(r) for r in REGS[:4]]
            sp = uc.reg_read(UC_ARM_REG_SP)
            calls.append((address, regs))

            if address == 0xff37d378:
                for addr, val in zip(regs, [pointer, 0x100000, 0, 0]):
                    put(uc, addr, val)
                uc.reg_write(UC_ARM_REG_R0, 0)
            elif address == 0xff3392c8:
                put(uc, get(uc, sp + 0xc), payload_len)
                put(uc, get(uc, sp + 0x30), 0)
                uc.reg_write(UC_ARM_REG_R0, 0)
            elif address == 0xff028254:
                uc.reg_write(UC_ARM_REG_R0, 0)
            elif address == 0x6db22c:
                num, den = regs[:2]
                den = max(1, den)
                uc.reg_write(UC_ARM_REG_R0, num // den)
                uc.reg_write(UC_ARM_REG_R1, num % den)
            else:
                uc.reg_write(UC_ARM_REG_R0, 0)

            # Return from external call
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

        u.hook_add(UC_HOOK_CODE, hook)
        u.emu_start(BASE + BODY, DONE, count=1000000)

        # 1. Verify MovieWriter was bypassed
        self.assertFalse(writer_called[0], "SD card writer should not be called")

        # 2. Verify MovieRecord advanced its internal frame counter (0x7bc0 + 0x70 = 0x7c30) from 3 to 4
        self.assertEqual(get(u, 0x7bc0 + 0x70), 4)

        # 3. Verify descriptor table recorded the intercepted frame
        self.assertEqual(get(u, BASE + CONTROL + 20), 1)  # total_frames = 1
        desc_addr = BASE + DESCRIPTORS
        self.assertEqual(get(u, desc_addr + 0), 1)        # status = Ready
        self.assertEqual(get(u, desc_addr + 12), payload_len)

if __name__ == '__main__':
    unittest.main()
