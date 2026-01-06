# Canon PowerShot SX430 IS: Live AV & Sensor Research

Research tools and experimental live streaming infrastructure for the **Canon PowerShot SX430 IS** (Firmware **GM1.00B**, Platform ID `13013`, DIGIC 4+).

---

## Current Status & Real-World Performance

> [!WARNING]
> **Performance Notice**: The current uncompressed liveview preview over Wi-Fi PTP operates at **low framerate (~2–5 fps)** with latency due to the uncompressed transfer size (~345 KB/frame) over the camera's low-power Wi-Fi interface. Native 1280x720 @ 25 fps hardware H.264 stream extraction without SD card write exhaustion remains an active area of research.

| Stream Mechanism | Resolution | Real-World Framerate | SD Card Writes | Latency | Status |
|---|---|---|---|---|---|
| **Direct Sensor LiveView** | 720x240 (Scaled to 720p) | ~2–5 fps | **Zero (0 bytes)** | ~200–500 ms | **Functional Baseline** |
| **Native DIGIC 4+ H.264** | 1280x720 | 25.0 fps (Target) | Exceeds buffer in ~14s | ~60–100 ms | **Research Target** |

---

## Validated Capabilities

- **Guarded Shooting Mode Transition**: Successfully switches from Playback to Shooting mode via native transition vector (`call_func_ptr(0xff05f154, 0x105f, 0)`), extending the lens and activating live CCD sensor DMA over Wi-Fi without manual dial manipulation.
- **Zero SD Card Wear**: In live sensor mode, frames are extracted directly from the DIGIC display framebuffer in RAM over PTP-IP. No video files or MP4 containers are written to the SD card.
- **Local HTTP MPEG-TS Server**: Serves live stream on `http://127.0.0.1:8554` for OBS Studio Media Source ingestion.
- **FFmpeg Frame Normalizer**: Scales the incoming sensor frames and provides a consistent MPEG-TS container for OBS Studio.

---

## Technical Bottleneck Analysis

1. **Why Uncompressed Viewport is ~2–5 FPS**:
   - Each uncompressed $720 \times 240$ YUV422 viewport buffer is $\approx 345\,\text{KB}$.
   - Over standard 802.11n IoT Wi-Fi on the camera, each PTP request-response roundtrip requires 150–300 ms, physically capping uncompressed throughput to 2–5 fps ($345\,\text{KB} \times 25\,\text{fps} = 8.6\,\text{MB/s}$ or 69 Mbps, which exceeds the camera's Wi-Fi radio capacity).
2. **Why Native H.264 Movie Mode Halts**:
   - The DIGIC 4+ hardware H.264 encoder outputs 1280x720 @ 25 fps at ~15–30 KB/frame (3–6 Mbps, easily fitting within Wi-Fi bandwidth).
   - However, stock movie recording concurrently commits an MP4 container to the SD card. Under concurrent network DMA, the SD card write FIFO overflows after $\approx 14$ seconds, halting recording (`playrec = 5`).
   - Decoupling the hardware H.264 encoder from the SD card filesystem write task is the primary goal of ongoing firmware research.

---

## Running the Baseline Stream

### 1. Start the Stream Server
```bash
python receiver/launch-obs-stream.py --camera-ip <CAMERA_IP>
```

### 2. Connect the Camera
1. Turn on the camera using the **Playback (`▶`) button**.
2. Press the **Wi-Fi button** and select your PC connection profile.
3. The server detects the camera, automatically switches to sensor mode, and begins streaming.

### 3. OBS Studio Configuration
- Add a **Media Source** in OBS Studio.
- **Uncheck** *Local File*.
- **Input**: `http://127.0.0.1:8554`
- **Input Format**: `mpegts`
- Click **OK**.

See [obs/OBS-SETUP.md](obs/OBS-SETUP.md) for full instructions.

---

## Verification & Testing

Run the automated test suite:
```bash
python -m unittest discover -s tests -v
python tools/check_sources.py
```

---

## License & Attribution

Project code is released under the **GPL-2.0-or-later** license. Upstream material retains its original licenses. See [LICENSE](LICENSE) and [THIRD_PARTY.md](THIRD_PARTY.md).
