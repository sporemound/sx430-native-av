#!/usr/bin/env python3
"""Read-only SX430 research tools. SPDX-License-Identifier: GPL-2.0-or-later."""
import argparse
import csv
import hashlib
import json
import math
import re
import struct
import subprocess
import sys
import zlib
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_BASE = 0xFF010000
ROM_END = 0x100000000
MAX_FRAME = 16 * 1024 * 1024
CRC_BLOCKS = ((0xFF010000, 0x5E45D8, 0x09B947F3),
              (0xFF7BBA78, 0x427F4, 0xB1CF0156))


def region(data, base, address, length):
    offset = address - base
    if length < 0 or offset < 0 or offset + length > len(data):
        raise ValueError(f"range {address:#x}+{length:#x} is outside supplied dump")
    return data[offset:offset + length]


def verify_firmware(data, base=ROM_BASE):
    if not 0 <= base < ROM_END or base + len(data) > ROM_END:
        raise ValueError("invalid 32-bit dump mapping")
    result = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
              "base": hex(base), "evidence": "upstream CHDK fingerprint comparison",
              "full_rom_covered": base <= ROM_BASE and base + len(data) == ROM_END,
              "canon_basic_final_word_omitted": base <= ROM_BASE and base + len(data) == ROM_END - 4,
              "hook_authorized": False, "blocks": []}
    try:
        result["version_matches"] = region(data, base, 0xFF0ACDE9, 8) == b"GM1.00B\0"
        result["platform_id_matches"] = region(data, base, 0xFFFE0270, 2) == struct.pack("<H", 13013)
        for address, length, expected in CRC_BLOCKS:
            actual = zlib.crc32(region(data, base, address, length)) & 0xFFFFFFFF
            result["blocks"].append({"address": hex(address), "length": length,
                                     "expected": f"{expected:08x}", "actual": f"{actual:08x}",
                                     "matches": actual == expected})
    except ValueError as e:
        result["error"] = str(e)
    # The documented Canon BASIC dumper ends at 0xfffffffc (exclusive).
    # All identity fields and both CRC blocks are still present. Do not pad input
    # or mislabel it as a full ROM; reject any other incomplete extent.
    covered = result["full_rom_covered"] or result["canon_basic_final_word_omitted"]
    result["matches_sx430_100b"] = (covered and
        result.get("version_matches", False) and result.get("platform_id_matches", False) and
        len(result["blocks"]) == 2 and all(b["matches"] for b in result["blocks"]))
    return result


def live_frame(data):
    if not 28 <= len(data) <= MAX_FRAME:
        raise ValueError("invalid live-view frame length")
    major, minor, aspect, palette, pal_start, vp_start, bm_start = struct.unpack_from("<7i", data)
    if major != 2 or minor < 0:
        raise ValueError("unsupported live-view protocol")
    header_size = 32 if minor >= 2 else 28
    if len(data) < header_size or vp_start < header_size or vp_start + 36 > len(data):
        raise ValueError("viewport descriptor outside frame")
    kind, start, width, visible, height, left, top, right, bottom = struct.unpack_from("<9i", data, vp_start)
    if kind != 0:
        raise ValueError("SX430 baseline expects YUV8 (UYVYYY), not this framebuffer type")
    if not (0 < visible <= width <= 8192 and 0 < height <= 8192 and width % 4 == 0):
        raise ValueError("invalid viewport dimensions")
    if min(left, top, right, bottom) < 0:
        raise ValueError("negative viewport margin")
    length = width * height * 3 // 2
    if start and (start < vp_start + 36 or start + length > len(data)):
        raise ValueError("viewport payload outside frame or overlapping its descriptor")
    return {"protocol": f"{major}.{minor}", "buffer_width": width,
            "visible_width": visible, "visible_height": height,
            "viewport_available": start != 0, "viewport_bytes": length if start else 0,
            "data_start": start, "lcd_aspect_code": aspect}


def exact_read(stream, n):
    data = stream.read(n)
    if len(data) != n:
        raise ValueError("truncated live-view dump")
    return data


def inspect_live(path):
    count, payload, available = 0, 0, 0
    dimensions = set()
    with open(path, "rb") as f:
        if exact_read(f, 4) != b"chlv":
            raise ValueError("not a chdkptp live-view dump")
        header_length, = struct.unpack("<I", exact_read(f, 4))
        if header_length != 8:
            raise ValueError("unsupported dump header size")
        if struct.unpack("<II", exact_read(f, 8)) != (1, 0):
            raise ValueError("unsupported dump format version")
        while True:
            size = f.read(4)
            if not size:
                break
            if len(size) != 4:
                raise ValueError("truncated frame length")
            n, = struct.unpack("<I", size)
            if not 28 <= n <= MAX_FRAME:
                raise ValueError("frame length exceeds bound or is too small")
            desc = live_frame(exact_read(f, n))
            dimensions.add((desc["buffer_width"], desc["visible_width"], desc["visible_height"]))
            count += 1
            available += int(desc["viewport_available"])
            payload += n
    if not count:
        raise ValueError("dump contains no frames")
    return {"source": "CHDK VIEWPORT DIAGNOSTIC ONLY", "native_movie_verified": False,
            "audio_present": False, "retrievals": count, "available_viewports": available,
            "live_protocol_bytes": payload, "dimensions_buffer_visible_height": sorted(dimensions),
            "sensor_fps": None, "dropped_sensor_frames": None,
            "note": "Dump has no camera timestamps or sequence numbers; retrieval count is not sensor frame count."}


def summarize_baseline(folder):
    result = inspect_live(folder / "baseline.lvdump")
    with (folder / "timing.csv").open(newline="") as timing:
        rows = list(csv.DictReader(timing))
    if len(rows) != result["retrievals"]:
        raise ValueError("timing/dump counts differ: interrupted or mixed capture")
    previous_end = None
    spans = []
    for i, row in enumerate(rows, 1):
        begin, end = float(row["begin_us"]), float(row["end_us"])
        if not all(math.isfinite(x) for x in (begin, end)) or end < begin:
            raise ValueError("invalid or backwards host clock")
        if int(row["index"]) != i or (previous_end is not None and begin < previous_end):
            raise ValueError("non-monotonic timing or sequence")
        previous_end = end
        spans.append((end - begin) / 1000)
    if sum(int(row["bytes"]) for row in rows) != result["live_protocol_bytes"]:
        raise ValueError("timing/dump byte counts differ")
    seconds = (float(rows[-1]["end_us"]) - float(rows[0]["begin_us"])) / 1e6
    if seconds <= 0:
        raise ValueError("capture duration must be positive")
    spans.sort()
    result.update({"capture_seconds": seconds,
                   "retrievals_per_second": len(rows) / seconds,
                   "live_protocol_mbps": result["live_protocol_bytes"] * 8 / seconds / 1e6,
                   "ptp_request_p50_ms": spans[(len(spans) - 1) // 2],
                   "ptp_request_p95_ms": spans[math.ceil(.95 * len(spans)) - 1],
                   "network_packet_loss": None, "camera_cpu_percent": None,
                   "camera_to_obs_latency_ms": None, "av_sync_ms": None,
                   "note": "Host request times include camera work and network transfer, not one-way latency. Clock source is chdkptp sys.gettimeofday; resolution may be coarse."})
    return result


def media_report(probe):
    streams = probe.get("streams", [])
    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    reasons = []
    if len(video) != 1 or len(audio) != 1:
        reasons.append("exactly one video and one audio stream required")
    if len(video) == 1:
        v = video[0]
        try:
            fps = Fraction(v.get("avg_frame_rate", "0/1"))
        except (ValueError, ZeroDivisionError):
            fps = None
        if (v.get("codec_name"), v.get("width"), v.get("height"), fps) != ("h264", 1280, 720, Fraction(25)):
            reasons.append("video metadata does not match H.264 1280x720 25 fps")
    if len(audio) == 1:
        a = audio[0]
        if (a.get("codec_name"), a.get("profile"), a.get("channels")) != ("aac", "LC", 1):
            reasons.append("audio metadata does not match mono AAC-LC")
    return {"target_metadata_matches": not reasons, "reasons": reasons, "streams": streams,
            "native_camera_provenance_verified": False, "live_wifi_verified": False,
            "decoded_integrity_verified": False, "av_sync_verified": False,
            "note": "Metadata alone does not establish camera origin, decodability, live delivery, or synchronization."}


def import_map(chdk):
    port = chdk / "trunk/platform/sx430is/sub/100b"
    revision = subprocess.check_output(["git", "-C", str(chdk), "rev-parse", "HEAD"], text=True).strip()
    pattern = re.compile(r"^(task_(MovieRecord|MovieWriter|FileWrite(Task)?|AudioTsk|AACTask|AACDrvTask|PtpipController|PtpipPacketDetector|PTPSessionTASK)|UIFS_(Start|Stop)MovieRecord_FW|Initialize(WLAN|PTPIPTransportResponder)_FW|ConnectPtpIPService_FW|add_ptp_handler|CreateMessageQueue|ReceiveMessageQueue|PostMessageQueue|TryPostMessageQueue|TakeSemaphore|GiveSemaphore|GetMemInfo|GetCCDTemperature|GetBatteryTemperature|GetOpticalTemperature)$")
    rows = []
    source = "trunk/platform/sx430is/sub/100b/funcs_by_name.csv"
    with (port / "funcs_by_name.csv").open() as source_file:
        source_rows = list(csv.reader(source_file))
    for line, fields in enumerate(source_rows, 1):
        if len(fields) >= 2 and pattern.fullmatch(fields[1]):
            address, name = fields[:2]
            rows.append({"address": address, "probable_symbol": name,
                "calling_convention": "unverified; inspect exact ARM disassembly and callers",
                "inputs": "unknown", "outputs": "unknown", "buffer_ownership": "unknown",
                "task_thread": name if name.startswith("task_") else "unknown",
                "cross_references": [], "confidence": "upstream name/address only; not hardware verified",
                "how_identified": "imported CHDK generated symbol list; not independently rediscovered",
                "source": f"https://github.com/petabyt/chdk/blob/{revision}/{source}#L{line}"})
    if not rows:
        raise ValueError("no expected SX430 symbols found")
    return {"camera": "sx430is", "firmware": "100b", "revision": revision,
            "exact_dump_verified": False, "symbols": rows}


def firmware_slice(data, base, address, length):
    # Runtime RAM copies documented in stubs_entry.S. End addresses are exclusive.
    mappings = [(0x006B1000, 0x006E01C4, 0xFF7CF0A8), (0x1900, 0x14F30, 0xFF7BBA78)]
    for start, end, source in mappings:
        if start <= address < end:
            if address + length > end:
                raise ValueError("slice crosses copied RAM segment")
            address = source + address - start
            break
    return region(data, base, address, length)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("verify-firmware", "firmware-slice", "firmware-strings"):
        q = sub.add_parser(name)
        q.add_argument("dump", type=Path)
        q.add_argument("--base", type=lambda x: int(x, 0), default=ROM_BASE)
        if name == "firmware-slice":
            q.add_argument("address", type=lambda x: int(x, 0))
            q.add_argument("length", type=lambda x: int(x, 0))
    sub.add_parser("inspect-live").add_argument("dump", type=Path)
    sub.add_parser("summarize-baseline").add_argument("folder", type=Path)
    sub.add_parser("import-map").add_argument("chdk", type=Path)
    q = sub.add_parser("inspect-media")
    q.add_argument("file", type=Path)
    q.add_argument("--ffprobe", default="ffprobe")
    args = p.parse_args()
    try:
        status = 0
        if args.command.startswith("firmware-") or args.command == "verify-firmware":
            if args.dump.stat().st_size > 32 * 1024 * 1024:
                raise ValueError("dump exceeds 32 MiB input bound")
            data = args.dump.read_bytes()
            report = verify_firmware(data, args.base)
            if args.command == "verify-firmware":
                result = report
                status = 0 if report["matches_sx430_100b"] else 2
            else:
                if not report["matches_sx430_100b"]:
                    raise ValueError("exact firmware fingerprint did not match; refusing SX430 address interpretation")
                if args.command == "firmware-slice":
                    if not 0 < args.length <= 65536:
                        raise ValueError("slice length must be 1..65536")
                    chunk = firmware_slice(data, args.base, args.address, args.length)
                    result = {"address": hex(args.address), "hex": chunk.hex(),
                              "sha256": report["sha256"], "interpretation": "raw bytes only"}
                else:
                    result = {"sha256": report["sha256"], "strings": [
                        {"rom_address": hex(args.base + m.start()), "text": m.group().decode("ascii")}
                        for m in re.finditer(rb"[ -~]{6,}", data)
                        if re.search(rb"movie|aac|audio|h264|ptpip|wlan|socket", m.group(), re.I)],
                        "note": "String locations are not function addresses or proven code cross-references."}
        elif args.command == "inspect-live":
            result = inspect_live(args.dump)
        elif args.command == "summarize-baseline":
            result = summarize_baseline(args.folder)
        elif args.command == "import-map":
            result = import_map(args.chdk.resolve())
        else:
            proc = subprocess.run([args.ffprobe, "-v", "error", "-show_streams", "-of", "json",
                                   str(args.file.resolve())], capture_output=True, text=True, timeout=60)
            if proc.returncode:
                raise ValueError(proc.stderr.strip())
            result = media_report(json.loads(proc.stdout))
            status = 0 if result["target_metadata_matches"] else 2
        print(json.dumps(result, indent=2))
        return status
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
