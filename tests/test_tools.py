import csv
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import sx430


def frame(start=100):
    buf = bytearray(124)
    struct.pack_into('<8i', buf, 0, 2, 2, 0, 0, 0, 32, 68, 0)
    struct.pack_into('<9i', buf, 32, 0, start, 4, 4, 4, 0, 0, 0, 0)
    return buf


def dump(f):
    return b'chlv' + struct.pack('<III', 8, 1, 0) + struct.pack('<I', len(f)) + f


class FirmwareTests(unittest.TestCase):
    def test_canon_basic_final_word_omission(self):
        data = bytearray(0xFF0000)
        data[0x9CDE9:0x9CDF1] = b'GM1.00B\0'
        struct.pack_into('<H', data, 0xFD0270, 13013)
        block = (sx430.ROM_BASE, 32, zlib.crc32(data[:32]))
        with patch.object(sx430, 'CRC_BLOCKS', (block, block)):
            report = sx430.verify_firmware(data[:-4])
            self.assertTrue(report['matches_sx430_100b'])
            self.assertTrue(report['canon_basic_final_word_omitted'])
            self.assertFalse(report['full_rom_covered'])
            for missing in (1, 3, 5, 8, 512):
                self.assertFalse(sx430.verify_firmware(data[:-missing])['matches_sx430_100b'])
        self.assertFalse(sx430.verify_firmware(data[:-4])['matches_sx430_100b'])

    def test_wrong_firmware_rejected(self):
        r = sx430.verify_firmware(bytes(0xFF0000))
        self.assertFalse(r['matches_sx430_100b'])
        self.assertFalse(r['hook_authorized'])

    def test_truncated_firmware_rejected(self):
        self.assertIn('error', sx430.verify_firmware(b'GM1.00B'))

    def test_regions_and_ram_mapping(self):
        with self.assertRaises(ValueError):
            sx430.region(b'123', 100, 99, 1)
        with self.assertRaises(ValueError):
            sx430.region(b'123', 100, 101, 3)
        data = bytes(range(256)) * 0x10000
        self.assertEqual(sx430.firmware_slice(data, sx430.ROM_BASE, 0x006B1004, 16),
                         sx430.region(data, sx430.ROM_BASE, 0xFF7CF0AC, 16))
        with self.assertRaises(ValueError):
            sx430.firmware_slice(data, sx430.ROM_BASE, 0x006E01C0, 8)

    def test_version_pid_and_crc_all_required(self):
        # Artificial bytes exercise verification control flow only, never camera evidence.
        data = bytearray(0xFF0000)
        data[0x9CDE9:0x9CDF1] = b'GM1.00B\0'
        struct.pack_into('<H', data, 0xFD0270, 13013)
        block = (sx430.ROM_BASE, 32, zlib.crc32(data[:32]))
        with patch.object(sx430, 'CRC_BLOCKS', (block, block)):
            self.assertTrue(sx430.verify_firmware(data)['matches_sx430_100b'])
            data[0] = 1
            self.assertFalse(sx430.verify_firmware(data)['matches_sx430_100b'])
        self.assertFalse(sx430.verify_firmware(data)['matches_sx430_100b'])


class LiveTests(unittest.TestCase):
    def inspect(self, content):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.lvdump'
            path.write_bytes(content)
            return sx430.inspect_live(path)

    def test_valid_viewport_is_never_native(self):
        r = self.inspect(dump(frame()))
        self.assertEqual(r['available_viewports'], 1)
        self.assertFalse(r['native_movie_verified'])
        self.assertFalse(r['audio_present'])
        self.assertIsNone(r['sensor_fps'])

    def test_unavailable_viewport(self):
        self.assertEqual(self.inspect(dump(frame(0)))['available_viewports'], 0)

    def test_truncation_at_every_offset(self):
        content = dump(frame())
        for length in range(len(content)):
            with self.subTest(length=length), self.assertRaises(ValueError):
                self.inspect(content[:length])

    def test_malicious_lengths_and_offsets(self):
        for offset, value in ((20, 0x7FFFFFFF), (36, 0x7FFFFFFF), (40, -1), (44, 8), (48, 8193)):
            f = frame()
            struct.pack_into('<i', f, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                sx430.live_frame(f)
        with self.assertRaises(ValueError):
            self.inspect(b'chlv' + struct.pack('<IIII', 8, 1, 0, 0xFFFFFFFF))

    def test_unknown_version_or_codec(self):
        for offset, value in ((0, 3), (32, 2)):
            f = frame()
            struct.pack_into('<i', f, offset, value)
            with self.assertRaises(ValueError):
                sx430.live_frame(f)

    def test_timing_and_dump_consistency(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'baseline.lvdump').write_bytes(dump(frame()))
            timing = folder / 'timing.csv'
            timing.write_text('index,begin_us,end_us,bytes\n1,0,40000,124\n')
            report = sx430.summarize_baseline(folder)
            self.assertEqual(report['retrievals_per_second'], 25)
            self.assertIsNone(report['sensor_fps'])
            timing.write_text('index,begin_us,end_us,bytes\n1,0,-1,124\n')
            with self.assertRaises(ValueError):
                sx430.summarize_baseline(folder)
            timing.write_text('index,begin_us,end_us,bytes\n1,0,40000,125\n')
            with self.assertRaises(ValueError):
                sx430.summarize_baseline(folder)


class MediaTests(unittest.TestCase):
    def test_codec_metadata_does_not_prove_camera(self):
        r = sx430.media_report({'streams': [
            {'codec_type': 'video', 'codec_name': 'h264', 'width': 1280, 'height': 720, 'avg_frame_rate': '25/1'},
            {'codec_type': 'audio', 'codec_name': 'aac', 'profile': 'LC', 'channels': 1}]})
        self.assertTrue(r['target_metadata_matches'])
        self.assertFalse(r['native_camera_provenance_verified'])
        self.assertFalse(r['av_sync_verified'])

    def test_missing_mic_or_invalid_rate_rejected(self):
        self.assertFalse(sx430.media_report({'streams': []})['target_metadata_matches'])
        r = sx430.media_report({'streams': [{'codec_type': 'video', 'avg_frame_rate': '0/0'}]})
        self.assertFalse(r['target_metadata_matches'])


if __name__ == '__main__':
    unittest.main()
