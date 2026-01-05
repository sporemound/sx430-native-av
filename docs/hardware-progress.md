# Canon PowerShot SX430 IS Hardware & Firmware Findings

## Platform & Firmware Identity
- **Model**: Canon PowerShot SX430 IS
- **Firmware**: GM1.00B
- **Platform ID**: `13013` (SX430 IS)
- **Processor**: DIGIC 4+ (ARM9 architecture)
- **CHDK Revision**: `6357`

---

## Validated Hardware & Firmware Findings

### 1. Shooting Mode Switch & Native Transition Vector
- **Initial State**: Camera boots into Playback mode (`rec = false`, `pr = 0/3`, `cc = 2`).
- **Mode Transition Handler**:
  - `switch_mode_usb(true)` sets the USB shooting mode request flag (`0x2410 = 0`, `0x2414 = 1`).
  - Native handler `0xff05f154` invoked with arguments `(0x105f, 0)` executes the firmware mode transition routine (`ModeDialToCamera`).
  - Verified hardware state: `rec = true`, `playrec (0x3ac8) = 2`, `cameracon (0x23cc) = 1`.
  - The lens extends and sensor DMA starts streaming into RAM.

### 2. Live Display Framebuffer & Sensor Extraction
- The DIGIC 4+ display controller populates viewport framebuffers in RAM (`YUV422 / UYVY` interleaved format).
- Frame dimensions: $720 \times 240$ buffer with $2\times$ pixel aspect ratio; decodes to $360 \times 240$ square-pixel RGB via `liveimg.get_viewport_pimg(..., true)`.
- PTP liveview transfer (`CHDK_LvdumpGetFrame`, opcode `0x9999`, subcommand `12`) retrieves viewport buffers directly without executing Lua scripts per frame.

### 3. Power Management & Standby Prevention
- Canon GUI timer enters Auto Power Down after 15-20 seconds if no button events occur.
- `set_auto_off(0)` disables the CHDK power down timer.
- Maintaining an active PTP live view streaming loop keeps the PTP-IP link alive without requiring intrusive shutter commands.

### 4. Zero SD Card Writes vs. Movie Recording
- Movie recording (`press('video')`) triggers hardware H.264 encoding while writing MP4 container structures to the SD card.
- Writing to SD card during concurrent network streaming causes DMA write FIFO starvation and buffer overruns after $\approx 14$ seconds.
- In pure Live Sensor mode (`stream-sensor-live.lua`), frames are captured directly from live display RAM without touching the SD card, achieving continuous uptime and zero SD card wear.
