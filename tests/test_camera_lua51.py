"""Optional scheduler regression checks using actual Lua 5.1, never LuaJIT.

Install Lupa, which provides lupa.lua51, to enable these tests.
Camera hardware, instruction values, and file I/O remain mocked.
"""
from pathlib import Path
import re
import unittest
try:
    from lupa.lua51 import LuaRuntime
except ImportError:
    LuaRuntime = None

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipIf(LuaRuntime is None,'Optional lupa.lua51 runtime not installed')
class CameraSchedulerTests(unittest.TestCase):
    def test_old_protected_wait_reproduces_camera_error(self):
        lua=LuaRuntime(unpack_returned_tuples=True)
        self.assertEqual(lua.eval('_VERSION'),'Lua 5.1')
        resumed,ok,error=lua.execute('''
            local co=coroutine.create(function()
                return pcall(function() coroutine.yield() end)
            end)
            return coroutine.resume(co)
        ''')
        self.assertTrue(resumed)
        self.assertFalse(ok)
        self.assertIn('yield across',error)

    def test_candidate_with_real_suspension_and_exact_csv_width(self):
        lua=LuaRuntime(unpack_returned_tuples=True)
        self.assertEqual(lua.eval('_VERSION'),'Lua 5.1')
        source=(ROOT/'camera/experimental/native-mode.lua.in').read_text()
        # Synthetic values only; the real generator verifies firmware separately.
        words='local firmware_words={\n'+''.join(
            '    {0x%08x,0x%08x},\n'%(a,i) for i,a in enumerate(range(0xff05f154,0xff05f748,4)))+'}\n'
        source=re.sub(r'-- FIRMWARE_WORDS_BEGIN.*?-- FIRMWARE_WORDS_END',lambda _:words,source,flags=re.S)
        lua.globals().candidate_source=source
        lua.execute((ROOT/'tests/camera_lua51_cases.lua').read_text())


if __name__=='__main__':unittest.main()
