# Route A Stock Canon Wi-Fi Protocol Characterization Results

## 1. Executive Summary & Route A Classification

Pursuant to the **SX430 Native A/V — Route A Execution Directive**, this investigation characterized the stock Canon PowerShot SX430 IS Wi-Fi communication and live-view streaming protocol with Canon Camera Connect without modifying camera firmware.

### Route A Decision Gate Classification
**`ROUTE-A-JPEG`**

- `[HW-OBSERVED]` **Video Path**: The stock Canon Camera Connect live view operates via PTP/IP vendor operation `0x9052` (`CanonGetLiveViewPicture`). The returned application payload contains a 128-byte Canon metadata header followed by a **$640 \times 480$ standard JPEG image** (SOI `0xFF 0xD8` to EOI `0xFF 0xD9`).
- `[HW-OBSERVED]` **H.264 Status**: No H.264 elementary stream (Annex B start codes `00 00 01` / `00 00 00 01`) or length-prefixed AVCC NAL units are present on the stock Wi-Fi live-view interface.
- `[HW-OBSERVED]` **Audio Status**: **`ROUTE A VIDEO ONLY`**. PTP/IP carries no microphone audio, AAC frames, or PCM samples.
- `[ROM-VERIFIED]` **Architectural Meaning**: The stock remote live-view path is serviced by Canon's viewfinder preview pipeline, completely decoupled from the hardware H.264 movie encoder (`task_MovieRecord` / `task_MovieWriter`).

### Directive Execution Action
Per **Phase A12** and **Phase B1**:
1. **Stop Route A streaming implementation**: Do not build a JPEG-to-OBS pipeline, do not transcode JPEG to H.264, and do not declare Route A as the final architecture.
2. **Use Route A as a protocol map**: Route A proves that PTP/IP connection management (`task_PtpipController` / `task_PtpipPacketDetector`) remains stable while optical sensor and viewfinder pipelines are active.
3. **Transition immediately to Route B**: Focus all primary video and audio research on the native hardware encoder boundaries: `task_MovieRecord` -> `task_MovieWriter` for 1280x720 25fps H.264 and `task_AudioTsk` -> `task_AACTask` for 48 kHz built-in microphone audio.

---

## 2. Evidence Taxonomy & Tagged Observations

All findings below are classified according to the research evidence standard:
- `[HW-OBSERVED]`: Measured directly from hardware sessions and packet traces.
- `[ROM-VERIFIED]`: Disassembled and confirmed in GM1.00B firmware ROM.
- `[UPSTREAM-SYMBOL]`: Derived from public CHDK / DryOS source anchors.
- `[HOST-MOCK]`: Host-side synthetic mechanisms (prohibited in final solution).
- `[HYPOTHESIS]`: Analytical model guiding Route B firmware hooks.

---

## 3. Network Topology & Flow Inventory (Phases A1–A3)

The complete session flow between Camera (`192.168.1.100`) and Client Host (`192.168.1.50`) was mapped in `analysis/route-a/connections.csv`:

| Connection ID | Protocol | Endpoints (Src -> Dst) | Service / Role | Bytes Transferred | Lifetime |
|---|---|---|---|---|---|
| `conn-01` | UDP | `192.168.1.100:1900` -> `239.255.255.250:1900` | SSDP Discovery NOTIFY | 1,248 B | 1.20 s |
| `conn-02` | UDP | `192.168.1.50:5353` -> `224.0.0.251:5353` | mDNS Announcement | 864 B | 0.85 s |
| `conn-03` | TCP | `192.168.1.50:49152` -> `192.168.1.100:8043` | UPnP Device Description HTTP | 4,038 B | 0.45 s |
| `conn-04` | TCP | `192.168.1.50:49153` -> `192.168.1.100:15740` | PTP/IP Command & Data Channel | 1,531,150 B | 22.50 s |
| `conn-05` | TCP | `192.168.1.50:49154` -> `192.168.1.100:15740` | PTP/IP Async Event Channel | 2,864 B | 22.40 s |

---

## 4. PTP/IP Transaction Ledger & Opcode Summary (Phases A4–A7)

Reconstructed PTP/IP traffic over `conn-04` (port 15740) yielded the following opcode summary (`analysis/route-a/opcodes.csv`):

| Opcode | Symbolic Name | Calls (Live View) | Rate (Hz) | Median Payload | Median Duration | Payload Type |
|---|---|---|---|---|---|---|
| `0x1002` | `OpenSession` | 0 (1 total) | 0.0 | 0 B | 15.2 ms | Session Control |
| `0x1014` | `GetDevicePropDesc` | 0 (1 total) | 0.0 | 128 B | 18.5 ms | Device Property Dataset |
| `0x9051` | `CanonStartLiveView` | 0 (1 total) | 0.0 | 0 B | 45.0 ms | LiveView State Switch |
| `0x9052` | `CanonGetLiveViewPicture` | 40 | 13.3 Hz | 38,100 B | 55.4 ms | Viewfinder JPEG + Meta Header |
| `0x9153` | `CanonCheckEvent` | 8 | 2.7 Hz | 96 B | 8.5 ms | Event Polling |
| `0x9053` | `CanonEndLiveView` | 0 (1 total) | 0.0 | 0 B | 32.1 ms | LiveView State Termination |
| `0x1003` | `CloseSession` | 0 (1 total) | 0.0 | 0 B | 14.0 ms | Session Close |

---

## 5. Codec Analysis: H.264 Search & JPEG Findings (Phases A8–A12)

1. `[HW-OBSERVED]` **Frame Inspection**:
   - Every `0x9052` transaction returns a payload beginning with a 128-byte header followed immediately by `0xFF 0xD8` (JPEG SOI) and concluding with `0xFF 0xD9` (JPEG EOI).
   - Extracted frames parse cleanly with `ffprobe` and decode with `ffmpeg` to $640 \times 480$ RGB images without errors.
2. `[HW-OBSERVED]` **Absence of H.264**:
   - Byte scans across all 40 captured live-view payloads detected **zero** instances of H.264 Annex B start codes (`00 00 01` / `00 00 00 01`) and zero AVCC length-prefixed NAL unit structures.
3. `[HW-OBSERVED]` **Frame Cadence**:
   - The stream rate is governed by client-side polling over PTP/IP request-response cycles, achieving ~13.3 fps (range 10–15 fps). It does NOT provide 25.000 fps continuous hardware-timed video.

---

## 6. Audio Search Results (Phase A13)

- `[HW-OBSERVED]` **Result: `ROUTE A VIDEO ONLY`**:
  - Zero audio packets, AAC access units, or PCM waveforms were transmitted during the entire stock live-view session.
  - Canon PTP/IP live view is strictly a visual viewfinder control protocol and does not service the camera microphone.

---

## 7. Immediate Transition to Route B (Phases B1–B5)

Because Route A does not expose native 720p25 H.264 or microphone audio, work moves strictly to **Route B: Native Hardware Encoder & Sound Subsystem Decoupling**.

### Route B Verified Anchors & Baseline
- `[ROM-VERIFIED]` **Movie Video Producer**: `task_MovieRecord` (`0xff1ecdbc`) registers hardware completion ISR callback at RAM `0x7180` (base table `0x7150 + 0x30`, default `0xff33ae58`) and posts video frame descriptors `[sp, #0x4c], [sp, #0x54]` to `0xff37d5e0`.
- `[ROM-VERIFIED]` **Movie Muxer / Consumer**: `task_MovieWriter` (`0xff37c6dc`) receives video frames and audio packets at `0xff37d5e0`, builds MP4 chunk tables (`0xff37d2b0`), and writes to SD card via `task_FileWrite` (`0xff35dd00`).
- `[ROM-VERIFIED]` **Audio / AAC Pipeline**:
  - `task_AudioTsk` (`0xff075bbc`) captures microphone ADC DMA.
  - `task_AACTask` (`0xff18e4fc`) compresses audio into AAC-LC access units using DryOS descriptor pool `0xff027fc8`.
- `[HW-OBSERVED]` **Reference Movie Baseline (`MVI_1280.MP4`)**:
  - Verified local movie contains **1280x720 @ 25.000 fps Constrained Baseline H.264** video (`pix_fmt=yuvj420p`, `time_base=1/25000`) and **48,000 Hz AAC-LC monaural audio in 2-channel container**.
- `[HW-OBSERVED]` **Passive Descriptor Milestone (`native-av-payload-012`)**:
  - Prior passive observation confirmed extraction of 1 full H.264 video frame (58,732 bytes, NAL type 1) and 67 contiguous AAC frames (22,870 bytes) matching the saved SD card movie bit-for-bit without corruption.

### Route B Execution Plan
1. **Passive RAM Buffer Extraction**: Hook the completion callback at `0x7180` and AAC descriptor queue to capture raw H.264 NAL units and AAC ADTS frames into bounded ring buffers during active movie recording.
2. **Decouple from `MovieWriter` SD Write**: Intercept `0xff37d5e0` to discard SD disk serialization while streaming frames over Wi-Fi, eliminating SD write bottlenecks.
3. **Audio Channel Normalization**: Map the single native microphone channel to 2-channel dual mono (`L = mic, R = mic`) at 48,000 Hz for OBS Media Source delivery.
