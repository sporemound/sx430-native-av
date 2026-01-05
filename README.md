# Canon PowerShot SX430 IS: Live AV Streaming & Sensor Research

Open-source research and streaming tools for the **Canon PowerShot SX430 IS** (Firmware **GM1.00B**, Platform ID `13013`, DIGIC 4+).

This project provides tools and scripts to stream real-time visual sensor output over Wi-Fi PTP to **OBS Studio** at 720p @ 25 fps with zero SD card writes, ultra-low latency, and continuous uptime.

---

## Key Features & Architecture

- **Direct CCD Sensor DMA Streaming**: Transitions the camera from Playback to Shooting mode via guarded native transition vector (`call_func_ptr(0xff05f154, 0x105f, 0)`), extending the lens and activating the image sensor without requiring manual dial manipulation.
- **Zero SD Card Wear & Zero Contention**: Video frames stream directly from the DIGIC live display buffer in RAM over Wi-Fi PTP (`CHDK_LvdumpGetFrame`). The SD card write FIFO is never touched, eliminating buffer overruns and thermal shutdown.
- **Constant 25.0 FPS Broadcast Normalization**: Real-time FFmpeg wallclock CFR normalizer scales frames to crisp 1280x720 HD with zero latency (`-preset ultrafast -tune zerolatency`) and zero macroblock artifacts.
- **Multi-Client HTTP Streaming Server**: Serves standard `video/mp2t` live MPEG-TS stream on `http://127.0.0.1:8554` for instant ingestion by OBS Studio Media Source.
- **Continuous Uptime**: Uninterrupted PTP frame loop with camera-side power management, preventing 15-second GUI standby shutdowns.

---

## Quick Start Guide

### Prerequisites
- Canon PowerShot SX430 IS with CHDK installed on the SD card (bootable).
- Python 3.10+ and [FFmpeg](https://ffmpeg.org/).
- [chdkptp](https://app.assembla.com/spaces/chdkptp/wiki) client for PTP communication.

### 1. Launch the Live Stream Server
```bash
python receiver/launch-obs-stream.py --camera-ip <CAMERA_IP>
```
*(Default camera IP: `10.0.0.202` or specify `--camera-ip <IP>`)*

### 2. Connect the Camera
1. Turn on the camera by pressing the **Playback (`▶`) button** on the back.
2. Press the **Wi-Fi button** and select your PC connection profile.
3. The server detects the connection, automatically extends the lens into live sensor mode, and begins streaming.

### 3. Setup OBS Studio
1. In OBS Studio, add a **Media Source** to your Scene.
2. **Uncheck** *Local File*.
3. **Input**: `http://127.0.0.1:8554`
4. **Input Format**: `mpegts`
5. Click **OK**.

For detailed configuration, see [OBS Studio Setup Guide](obs/OBS-SETUP.md).

---

## Repository Structure

```text
├── camera/                  # Camera-side Lua scripts for CHDK
│   ├── stream-sensor-live.lua # Direct live sensor streaming script
│   └── baseline.lua         # Baseline capability probes
├── receiver/                # Host-side receiver and streaming server
│   └── launch-obs-stream.py # HTTP MPEG-TS live streaming server
├── obs/                     # OBS Studio integration guides
│   └── OBS-SETUP.md         # OBS Media Source setup instructions
├── docs/                    # Technical research and hardware documentation
│   ├── architecture.md      # Pipeline architecture and data flow
│   ├── hardware-progress.md # Hardware reverse engineering findings
│   ├── memory-map.md        # DIGIC 4+ RAM word and handler map
│   └── mode-transition.md   # Firmware state machine analysis
├── tools/                   # Offline verification and analysis tools
│   ├── sx430.py             # Firmware analysis toolkit
│   └── check_sources.py     # Source integrity checks
└── tests/                   # Automated test suite
```

---

## Research & Verification

Run the test suite from the repository root:
```bash
python -m unittest discover -s tests -v
python tools/check_sources.py
```

See [docs/hardware-progress.md](docs/hardware-progress.md) for detailed firmware analysis and reverse engineering findings.

---

## License & Attribution

Project code is released under the **GPL-2.0-or-later** license. Upstream material retains its original licenses. See [LICENSE](LICENSE) and [THIRD_PARTY.md](THIRD_PARTY.md).
