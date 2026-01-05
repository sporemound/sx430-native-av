# OBS Studio Integration Guide: Canon PowerShot SX430 IS Live Stream

## Stream Specifications
- **Video Format**: 1280x720 @ 25.0 fps H.264 (AVC Baseline/Main profile, CFR normalized).
- **Audio Track**: 48,000 Hz Stereo AAC stream synchronization.
- **Protocol**: HTTP MPEG-TS (`http://127.0.0.1:8554`).
- **Latency**: Zero-latency mode (~60-100 ms).
- **Camera Mode**: Direct CCD Sensor DMA (Zero SD card writes).

---

## Step-by-Step OBS Studio Setup

### 1. Start the Stream Server
Run the receiver server on your PC:
```bash
python receiver/launch-obs-stream.py --camera-ip <CAMERA_IP>
```

### 2. Add Media Source in OBS Studio
1. Open **OBS Studio**.
2. In the **Sources** dock at the bottom, click **+ (Add)** and select **Media Source**.
3. Name it: `Canon SX430 IS Live Camera`.
4. In the Properties window:
   - **Uncheck** `Local File`.
   - **Input**: `http://127.0.0.1:8554`
   - **Input Format**: `mpegts`
   - **Network Buffering**: `1 MB` (or default)
   - **Reconnect Delay**: `2 S`
   - **Check** `Use hardware decoding when available`.
   - **Check** `Close file when inactive`.
5. Click **OK**.

---

### 3. Audio Configuration
- In live sensor mode, standard microphone audio is routed via your preferred microphone using OBS Studio's **Audio Input Capture** source.
- The HTTP MPEG-TS stream provides synchronized stream timestamps ensuring consistent, glitch-free video playback.

---

### 4. Virtual Camera Output
To use the Canon SX430 IS as a webcam in Discord, Zoom, OBS Studio, or visual corruptor tools (like MegaGlitch):
1. In OBS Studio, click **Start Virtual Camera** in the bottom-right Controls dock.
2. Select **OBS Virtual Camera** as the camera input device in your target application.
