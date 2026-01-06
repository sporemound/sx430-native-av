# Canon PowerShot SX430 IS Hardware & Firmware Findings

## Platform & Firmware Identity
- **Model**: Canon PowerShot SX430 IS
- **Firmware**: GM1.00B
- **Platform ID**: `13013` (SX430 IS)
- **Processor**: DIGIC 4+ (ARM9 architecture)
- **CHDK Revision**: `6357`

---

## Hardware Findings & Throughput Analysis

### 1. Shooting Mode Switch & Native Transition Vector
- **Initial State**: Camera boots into Playback mode (`rec = false`, `pr = 0/3`, `cc = 2`).
- **Mode Transition Handler**:
  - `switch_mode_usb(true)` sets the USB shooting mode request flag (`0x2410 = 0`, `0x2414 = 1`).
  - Native handler `0xff05f154` invoked with arguments `(0x105f, 0)` executes the firmware mode transition routine (`ModeDialToCamera`).
  - Verified hardware state: `rec = true`, `playrec (0x3ac8) = 2`, `cameracon (0x23cc) = 1`.
  - The lens extends and sensor DMA starts streaming into RAM.

### 2. Viewport Transport Throughput & Bottleneck
- Uncompressed viewport frame size: $720 \times 240$ YUV422 = $345,600$ bytes.
- PTP request-response latency over Wi-Fi: ~150–300 ms per frame.
- Measured real-world framerate: **~2–5 fps**.
- Bandwidth required for uncompressed 25 fps: $345\,\text{KB} \times 25 = 8.64\,\text{MB/s}$ (69.1 Mbps), which exceeds the camera's internal 802.11n Wi-Fi bandwidth.

### 3. Native H.264 Encoder Investigation
- Hardware H.264 encoder stream size: ~15–30 KB/frame (3–6 Mbps at 25 fps).
- **Core Challenge**: In stock firmware, movie encoding is tightly coupled with SD card file writing (`WRITE_SD` task). Concurrent Wi-Fi extraction leads to SD write buffer overflow after ~14 seconds.
- **Future Research Focus**: Hooking the DIGIC 4+ video completion callback (`0x7180` / `0xc6c8`) and redirecting encoded NAL units to network buffers without engaging the SD card file write pipeline.
