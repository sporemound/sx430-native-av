# Live Streaming Architecture & Pipeline

```text
+-------------------------+
|  Canon PowerShot SX430  |
|  - CCD Sensor DMA       |
|  - DIGIC 4+ Framebuffer |
+------------+------------+
             |
             | Wi-Fi PTP-IP (802.11n)
             v
+-------------------------+
|  chdkptp Engine         |
|  - stream-sensor-live   |
|  - Viewport extraction  |
+------------+------------+
             |
             | PPM Named Pipe / Stream
             v
+-------------------------+
|  FFmpeg Stream Engine   |
|  - Wallclock CFR (25fps)|
|  - x264 Zerolatency     |
|  - 720p Bicubic Scaling |
+------------+------------+
             |
             | Local HTTP (MPEG-TS)
             v
+-------------------------+
|  OBS Studio             |
|  - Media Source         |
|  - http://127.0.0.1:8554|
+-------------------------+
```

## Component Responsibilities

1. **Camera Layer**:
   - Executes mode switch via `switch_mode_usb(true)` and `call_func_ptr(0xff05f154, 0x105f, 0)`.
   - Sensor DMA streams uncompressed live preview frames into memory.
2. **PTP Transport Layer**:
   - `chdkptp` queries `con:live_get_frame_pcall(1)` in a high-speed non-blocking loop.
   - Extracts square-pixel RGB frames via `liveimg.get_viewport_pimg`.
3. **Stream Normalizer Layer**:
   - FFmpeg ingests frames and applies constant framerate (CFR 25.0 fps) wallclock timestamps.
   - Encodes via `libx264` (`-preset ultrafast -tune zerolatency -pix_fmt yuv420p -g 25`).
   - Muxes to broadcast-grade MPEG-TS container with synchronized 48 kHz stereo AAC audio.
4. **Broadcast Server Layer**:
   - Multi-threaded Python HTTP server accepts OBS connections on port 8554.
   - Broadcasts MPEG-TS stream packets directly to all active clients with zero disk latency.
