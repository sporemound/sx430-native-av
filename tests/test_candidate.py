import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import generate_mode_candidate as candidate


class CandidateTests(unittest.TestCase):
    def test_rejects_unverified_firmware(self):
        with self.assertRaisesRegex(ValueError,'does not match'):
            candidate.generate(b'not firmware')

    def test_rejects_changed_handler_even_if_identity_passes(self):
        with patch.object(candidate.sx430,'verify_firmware',return_value={'matches_sx430_100b':True}):
            with self.assertRaisesRegex(ValueError,'differs'):
                candidate.generate(bytes(0x60000))

    def test_generated_table_covers_exact_reviewed_region(self):
        rom=bytearray(0x60000)
        start,stop=0xff05f154,0xff05f748
        for i,addr in enumerate(range(start,stop,4)):
            struct.pack_into('<I',rom,addr-candidate.sx430.ROM_BASE,i)
        digest=hashlib.sha256(rom[start-candidate.sx430.ROM_BASE:stop-candidate.sx430.ROM_BASE]).hexdigest()
        with patch.object(candidate.sx430,'verify_firmware',return_value={'matches_sx430_100b':True}),patch.object(candidate,'EXPECTED_HANDLER_SHA256',digest):
            script=candidate.generate(rom)
        self.assertEqual(script.count('    {0xff'),381)
        self.assertIn('{0xff05f154,0x00000000}',script)
        self.assertIn('{0xff05f744,0x0000017c}',script)
        self.assertLess(script.index('for _,v in ipairs(firmware_words)'),script.index('switch_mode_usb(true)'))
        self.assertIn('assert(#firmware_words==381',script)

    def test_cli_does_not_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as td:
            rom=Path(td)/'input.bin';rom.write_bytes(b'fixture')
            out=Path(td)/'candidate.lua';out.write_text('existing')
            with patch.object(sys,'argv',['generate','--rom',str(rom),'--out',str(out)]),patch.object(candidate,'generate',return_value='replacement'):
                with self.assertRaises(FileExistsError):candidate.main()
            self.assertEqual(out.read_text(),'existing')


if __name__=='__main__':unittest.main()
