# SX430 native A/V over Wi-Fi

Research tools for the Canon PowerShot SX430 IS, firmware **GM1.00B**. The target is native 1280×720/25 H.264 video and built-in microphone AAC audio over Wi-Fi to OBS.

**Native streaming is not implemented.** This repository contains verification tools, pinned source references, sanitized findings, and an experimental mode-transition candidate. It does not provide a working webcam, encoder hooks, an OBS source, or a replacement firmware image.

## Current findings

- Firmware identity and CRC verification, CHDK boot, offline shooting, and PTP/IP communication have been demonstrated during private testing.
- Stock shooting requests over Wi-Fi caused a return to playback. A normal ModeDialToCamera event did not maintain shooting.
- Bounded ARM execution reproduced an upstream event translation and verified the mode pre-handler's two RAM writes for selected inputs.
- A guarded direct-handler candidate is prepared but **has not been tested on a camera**. Concurrent camera behavior remains unresolved.
- Encoder buffers, microphone extraction, sustained transport, synchronization, and OBS integration remain future work.

See [research status](docs/hardware-progress.md), [mode investigation](docs/mode-transition.md), and [experiment ledger](docs/experiments.md). Raw camera evidence and firmware are excluded. Hardware observations here are summaries, not independently reproducible public capture records.

## Offline tools

Use Python 3.10 or later from the repository root:

```sh
python -m unittest discover -s tests -v
python tools/check_sources.py
python tools/sx430.py --help
```

To verify your own locally held dump, place it in the ignored `private/` directory:

```sh
python tools/sx430.py verify-firmware private/PRIMARY.BIN
```

The default ROM base is `0xff010000`. A dump starting at `0xff000000` requires the corresponding `--base` option. See [memory map](docs/memory-map.md) for the documented final-four-byte omission and CRC limitations. Standard-library tests use synthetic bytes. A viewport packet or codec metadata alone does not prove native camera streaming.

## Experimental mode candidate

[Experimental instructions](camera/experimental/README.md) describe generating the candidate locally from verified firmware and running it through a separately installed modern chdkptp client. The ungenerated template refuses to run. The candidate requires explicit CHDK native-call enablement and changes camera RAM; offline checks do not establish safe or stable hardware behavior.

For a getter-only viewport baseline, use `tools/capture_baseline.py --help` with your own client path and camera address. The host Lua follows r1528 return conventions. Viewport output is not native movie video and contains no microphone audio.

## Source and licensing

The pinned [SX430 port](https://github.com/petabyt/chdk/tree/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is) has no implemented SX430 movie-record replacement or AAC extraction path. Related-port code and task names are research leads, not proof of compatible hooks.

Project code is GPL-2.0-or-later; upstream material retains its licenses and attribution. See [LICENSE](LICENSE) and [THIRD_PARTY.md](THIRD_PARTY.md). No Canon firmware, device logs, media, credentials, or machine-specific setup is redistributed. See [publication scope](PUBLICATION.md).
