# SX430 Native A/V — Phase C & D Architecture Specification

## 1. Executive Summary & Objective

Following the empirical hardware validation of **Phase B2 (Native H.264 720p25)** and **Phase B3/B4 (Native 48 kHz AAC Audio)** on the Canon PowerShot SX430 IS (GM1.00B), this document specifies the architecture for:
- **Phase C: Continuous Wi-Fi Transport & SD Storage Decoupling**
- **Phase D: OBS Studio Zero-Transcode Delivery Contract**

```
+---------------------------------------------------------------------------------------------------+
| CAMERA FIRMWARE (DIGIC 4+ / DryOS R59)                                                            |
|                                                                                                   |
|  Optical Sensor ---> Hardware H.264 Encoder ---> ISR Hook (0x7180)                                |
|                      (1280x720 @ 25 fps)            │                                             |
|                                                     ▼                                             |
|  Microphone ADC ---> task_AACTask (0xff18e4fc) -> Descriptor ---> Bounded RAM Ring Buffer (256KB) |
|                      (48 kHz AAC-LC)                Pool          │                               |
|                                                                   ▼                               |
|                                                      [ SD Write Decoupler (0xff37d5e0) ]          |
|                                                                   │ (SD writes bypassed)          |
|                                                                   ▼                               |
|                                                      Wi-Fi AVST Transmitter (Port 15740/TCP)      |
+-------------------------------------------------------------------|-------------------------------+
                                                                    │ 802.11n Wi-Fi
                                                                    ▼
+---------------------------------------------------------------------------------------------------+
| HOST RECEIVER & OBS INTEGRATION (PC)                                                              |
|                                                                                                   |
|  AVST Wire Protocol Parser ---> Jitter & PTS Synchronizer ---> Zero-Transcode MPEG-TS Remuxer      |
|                                                                │ (Pass-through H.264 + 48kHz AAC) |
|                                                                ▼                                  |
|                                                    Localhost Stream (http://127.0.0.1:8554)       |
|                                                                │                                  |
|                                                                ▼                                  |
|                                                    OBS Studio Media Source                        |
|                                                    (1280x720 @ 25.0 fps, 48kHz Dual-Mono Audio)   |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Phase C: SD Write Decoupling & Continuous Ring Transport

### A. SD Write Decoupling Mechanism (`[ROM-VERIFIED]`)
- **Stock Path**: `task_MovieRecord` (`0xff1ecdbc`) posts video and audio descriptor packets to `task_MovieWriter` via `bl #0xff37d5e0` (`0xff1ecce8` / `0xff1ed674`). `task_MovieWriter` packages MP4 container boxes and submits them to `task_FileWrite` (`0xff35dd00`) for SD card writing.
- **Decoupling Hook**:
  - In streaming mode, the completion hook replaces `0xff37d5e0` with an acknowledgment proxy.
  - The proxy copies the descriptor fields (`source_address`, `length`, `pts`, `nal_type`) into the Wi-Fi transmission ring and immediately returns success (`r0=0`) to `task_MovieRecord`.
  - **Result**: The DIGIC 4+ hardware encoder continues generating successive frames continuously without writing bytes to SD storage and without triggering SD FIFO buffer overflows.

### B. AVST (Audio/Video Stream Transport) Protocol Specification
The transmission stream over TCP uses a lightweight, fixed-header binary framing protocol (`AVST` v1):

```text
+-------------------------------------------------------------------+
| AVST Header (16 bytes, Little-Endian)                             |
|   0x00..0x03: Magic Identifier = 0x41565354 ('AVST')              |
|   0x04..0x05: Stream ID (1 = H.264 Video, 2 = AAC Audio)          |
|   0x06..0x07: Sequence Number (uint16, rolls over at 65535)       |
|   0x08..0x0B: Hardware Timestamp (uint32, 90 kHz clock ticks)     |
|   0x0C..0x0F: Payload Length (uint32, length of following bytes)  |
+-------------------------------------------------------------------+
| Payload Bytes (Length defined in Header)                          |
|   If Stream 1: Complete H.264 NAL Unit (Annex B start code 00000001) |
|   If Stream 2: Complete AAC Frame with ADTS Header (48 kHz stereo)|
+-------------------------------------------------------------------+
```

### C. Flow Control & Loss Protection
1. **Zero Camera Blocking**: The camera-side ISR / hook must never block or wait on network I/O.
2. **Whole Access-Unit Drop**: If the network queue fills during a Wi-Fi transmission hiccup, the transmitter drops complete video frames (P-frames) rather than partial packets.
3. **IDR Resynchronization**: If a frame is dropped, the receiver requests or waits for the next IDR keyframe before resuming video presentation.
4. **Independent Audio Queue**: AAC audio packets are prioritized in a dedicated ring buffer to maintain continuous, uninterrupted 48 kHz acoustic playback.

---

## 3. Phase D: OBS Studio Output Contract & Delivery

### A. Output Stream Specification
- **Video Parameters**:
  - Codec: H.264 / MPEG-4 AVC (Constrained Baseline, Level 4.1)
  - Dimensions: **$1280 	imes 720$**
  - Frame Rate: **25.000 fps** (Constant Frame Rate, hardware-timed)
  - Pixel Format: `yuvj420p` (Full Range BT.709)
  - Transcoding: **NONE** (Pass-through camera bitstream directly)
- **Audio Parameters**:
  - Codec: AAC-LC
  - Sample Rate: **48,000 Hz**
  - Channel Count: **2 Channels (Dual-Mono: `L = mic, R = mic`)**
  - Bitrate: 128 kbps
  - Transcoding: **NONE** (Pass-through native AAC ADTS frames directly)
- **Synchronization**:
  - Common hardware timebase (`time_base=1/90000` / `time_base=1/25000`)
  - Zero accumulating PTS drift across sustained sessions.

### B. Ingestion Interface
The host receiver hosts a local timestamp-preserving MPEG-TS stream endpoint:
```text
http://127.0.0.1:8554/live.ts
```
In OBS Studio:
- Add Source $ightarrow$ **Media Source** (or **VLC Video Source**)
- Uncheck *Local File*
- Input URL: `http://127.0.0.1:8554/live.ts`
- Network Buffering: `1 MB` (Low Latency)

---

## 4. Architectural Safety & Stability Gates

| Gate | Description | Status |
|---|---|---|
| **Gate 1: ROM Disassembly & Symbol Proof** | Exact instruction addresses for `MovieRecord`, `MovieWriter`, `AACTask`, completion ISR | **PASSED** (`[ROM-VERIFIED]`) |
| **Gate 2: Native Video Extraction** | 77,368-byte H.264 slice matched bit-for-bit with MP4 on SD card | **PASSED** (`[HW-OBSERVED]`) |
| **Gate 3: Native Audio Extraction** | 67 contiguous AAC frames @ 48kHz, 0 gaps, physical clap verified | **PASSED** (`[HW-OBSERVED]`) |
| **Gate 4: SD Write Decoupling** | Bypassing `0xff37d5e0` SD writes while keeping encoder loop active | **NEXT IMPLEMENTATION** |
| **Gate 5: Sustained Streaming** | Continuous streaming over Wi-Fi (> 10 minutes without desync) | **NEXT VALIDATION** |
