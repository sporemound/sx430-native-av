"""Execute bounded ARM paths from the locally verified firmware; never connects to a camera.

Requires Unicorn 2.1.4 installed in the active Python environment. This is a function-level model,
not a camera emulator. Initial RAM and intercepted function boundaries are
recorded explicitly; results do not establish the camera's runtime controller order.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
import sx430
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rom', type=Path, required=True)
parser.add_argument('--out', type=Path, default=ROOT/'private/emulated-mode-paths.json')
args = parser.parse_args()
import unicorn
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR

ROM = args.rom.read_bytes()
assert sx430.verify_firmware(ROM)['matches_sx430_100b'], 'Wrong firmware: no execution'
SHA = hashlib.sha256(ROM).hexdigest()
BASE, END, STACK = 0xff010000, 0x700000, 0x600000


def execute(name, entry, args, words, ranges, intercept=None):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(BASE, 0xff0000)
    uc.mem_write(BASE, ROM)
    uc.mem_protect(BASE, 0xff0000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
    uc.mem_map(0, 0x800000)
    # Firmware startup copy, followed by explicit synthetic live state.
    uc.mem_write(0x1900, ROM[0xff7bba78-BASE:0xff7bba78-BASE+0x14f30-0x1900])
    for addr, value in words.items():
        uc.mem_write(addr, struct.pack('<I', value))
    uc.reg_write(UC_ARM_REG_SP, STACK)
    uc.reg_write(UC_ARM_REG_LR, END)
    for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
        uc.reg_write(reg, value)
    trace, writes, calls = [], [], []

    def code(machine, address, size, _):
        trace.append(address)
        if intercept is not None and address == intercept:
            calls.append([machine.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1)])
            machine.emu_stop()  # Stop at boundary; never invent a callee result.
            return
        if not any(start <= address < stop for start, stop in ranges):
            raise AssertionError(f'Unexpected code {address:08x} in {name}')

    def write(machine, access, address, size, value, _):
        if not STACK-0x100 <= address < STACK:
            writes.append({'address': hex(address), 'size': size, 'value': value})

    uc.hook_add(UC_HOOK_CODE, code)
    uc.hook_add(UC_HOOK_MEM_WRITE, write)
    uc.emu_start(entry, END, count=1000)
    from unicorn.arm_const import UC_ARM_REG_PC
    assert uc.reg_read(UC_ARM_REG_PC) == END or calls, 'Execution did not reach expected boundary'
    result = dict(name=name, entry=hex(entry), arguments=list(args),
                  initial_words={hex(k): v for k, v in words.items()},
                  return_value=uc.reg_read(UC_ARM_REG_R0) if not calls else None,
                  intercepted_calls=calls, nonstack_writes=writes,
                  instruction_count=len(trace), executed_addresses=[hex(a) for a in trace])
    return result


results = []
filter_ranges = [(0xff202fd0, 0xff20306c), (0xff203124, 0xff203138),
                 (0xff201834, 0xff2018e4), (0xff0b01e0, 0xff0b0204),
                 (0xff0b024c, 0xff0b0264)]
for mode in (0, 1):
    r = execute(f'event_filter_flag_{mode}', 0xff202fd0, (0x105f,),
                {0x8630: mode}, filter_ranges)
    assert r['return_value'] == 0 and r['nonstack_writes'] == []
    results.append(r)

pre_ranges = [(0xff05f154, 0xff05f29c), (0xff05f73c, 0xff05f748)]
for state in (2, 8, 12, 15):
    for flag in (0, 1):
        words = {0x23cc: state, 0x2410: flag, 0x2414: 0, 0x241c: 0}
        r = execute(f'prehandler_state_{state}_flag_{flag}', 0xff05f154,
                    (0x105f, 0), words, pre_ranges)
        assert r['nonstack_writes'] == [
            {'address': '0x2410', 'size': 4, 'value': 0},
            {'address': '0x2414', 'size': 4, 'value': 1}]
        results.append(r)

for event in (0x1051, 0x105e, 0x105f, 0x1062, 0x10a2, 0x10a3, 0x1001):
    r = execute(f'application_controller_{event:04x}', 0xff02a7e8,
                (0, event, 0, 0), {0x1b10: 0},
                [(0xff02a7e8, 0xff02aa3c), (0xff02aba4, 0xff02abb4),
                 (0xff02ac0c, 0xff02ac14)], intercept=0xff06193c)
    expected = 0xffffffff if 0x1051 <= event <= 0x10a2 else event
    assert r['intercepted_calls'] == [[expected, 0]]
    assert r['nonstack_writes'] == []
    results.append(r)

out = args.out
out.parent.mkdir(parents=True, exist_ok=True)
assert not out.exists(), 'Choose a fresh report filename'
out.write_text(json.dumps(dict(
    firmware_sha256=SHA, emulator=unicorn.__version__,
    scope='Bounded ROM functions, synthetic RAM; no OS, hardware, or concurrency emulation',
    external_function_stubs=[],
    controller_boundary='Stop before CameraCon at 0xff06193c and record r0/r1',
    passed=len(results), cases=results), indent=2)+'\n')
print(f'{len(results)} bounded ARM cases passed; report: {out}')
