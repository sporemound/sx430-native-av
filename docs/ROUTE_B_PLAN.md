# SX430 Native A/V — Route B Execution Plan

## 1. Objective & Target Specification

Route B accomplishes direct extraction of native camera-side encoded video and built-in microphone audio by tapping the DIGIC 4+ hardware encoder and audio compression subsystem.

### Fixed Target Contract (OBS Delivery)
- **Video**: $1280 \times 720$ @ 25.000 fps, H.264 / MPEG-4 AVC Constrained Baseline, camera-origin encoded stream (no host re-encoding).
- **Audio**: Built-in Canon SX430 IS microphone, camera-origin AAC-LC / PCM samples, 48,000 Hz, 2-channel dual-mono (`L = mic, R = mic`).
- **Transport**: 802.11n Wi-Fi stream over PTP/IP or native DryOS network transport.

---

## 2. ROM Firmware Architecture & Injection Points

All firmware anchors below are statically verified in the GM1.00B ROM dump (`SHA256: a67792b34e74a35ff93d7362e9bd1b6e2e3196cee471074d03e0a8fca1de031b`):

### A. Video Pipeline (`task_MovieRecord` -> `task_MovieWriter`)
- `[ROM-VERIFIED]` **Movie Launch**: `UIFS_StartMovieRecord_FW` (`0xff0687bc`) initiates `task_MovieRecord` (`0xff1ecdbc`).
- `[ROM-VERIFIED]` **State Structure**: State pointer at `0x7bc0` (`MovieRecorder.c`), framerate parameter at `+0x60` (supporting 10, 15, 20, 24, 25, 30, 60 fps).
- `[ROM-VERIFIED]` **Hardware Completion ISR**: ISR entry at `0xff1a9f84` calls the completion handler stored in RAM table `0x7150 + 0x30` (`0x7180`), defaulting to `0xff33ae58`.
- `[ROM-VERIFIED]` **Async Video Callback**: Registered at RAM address `0xc6c8` (default `0xff1ec658`).
- `[ROM-VERIFIED]` **Message Queue Dispatch**: `task_MovieRecord` posts video descriptors `[sp, #0x4c], [sp, #0x54]` to `task_MovieWriter` queue via `bl #0xff37d5e0` (at `0xff1ecce8` and `0xff1ed674`).
- `[ROM-VERIFIED]` **SD Write Interface**: `task_MovieWriter` (`0xff37c6dc`) packages MP4 chunks and hands buffers to `task_FileWrite` (`0xff35dd00`).

### B. Audio Pipeline (`task_AudioTsk` -> `task_AACTask`)
- `[ROM-VERIFIED]` **Microphone ADC Capture**: `task_AudioTsk` (`0xff075bbc`) receives DMA buffers from the physical microphone.
- `[ROM-VERIFIED]` **Subsystem Arming**: Movie start hooks audio via `0xff078828` (called from `MovieRecorder.c` at `0xff1ec8b8`).
- `[ROM-VERIFIED]` **AAC Compression Engine**: `task_AACTask` (`0xff18e4fc`) and `task_AACDrvTask` (`0xff3174b0`) encode PCM into AAC access units using DryOS descriptor heap (`0xff027fc8`).
- `[ROM-VERIFIED]` **Audio Frame Dispatch**: Audio descriptors are enqueued to `task_MovieWriter` via `0xff37d164` / `0xff37d5e0`.

---

## 3. Phased Execution Roadmap

### PHASE B1 — Passive In-Memory Buffer Observation (Baseline)
- **Goal**: Passively monitor video and audio buffer pointers without interrupting the stock movie recording path or modifying return values.
- **Safety Gate**: The camera records a normal movie to the SD card. An in-memory ring observer copies descriptor metadata (pointer, length, timestamp, sequence) and writes a bounded diagnostic trace to RAM.
- **Verification**: Ensure camera shuts down cleanly, SD card movie plays without corruption, and descriptor metadata matches the saved MP4 track bit-for-bit.

### PHASE B2 — Native H.264 Access Unit Extraction & Verification
- **Goal**: Extract complete camera-owned H.264 NAL units (SPS, PPS, IDR, non-IDR slices) directly from encoder memory.
- **Verification Commands**:
  ```bash
  ffprobe -v error -show_format -show_streams extracted_video.h264
  ffmpeg -v error -i extracted_video.h264 -frames:v 1 decoded_frame.png
  ```
- **Acceptance Criteria**: SPS reports $1280 \times 720$, Constrained Baseline, `pix_fmt=yuvj420p`, $25.000$ fps timebase, and decoded frames match the physical scene.

### PHASE B3 — Native Microphone Audio Extraction
- **Goal**: Capture contiguous AAC access units or raw PCM blocks directly from `task_AACTask` / `task_AudioTsk`.
- **Acoustic Verification**: Record a physical synchronization event (e.g. sharp hand clap in front of the lens) and verify that the extracted waveform contains the corresponding acoustic peak.
- **Verification Commands**:
  ```bash
  ffprobe -v error -show_streams extracted_audio.aac
  ffmpeg -v error -i extracted_audio.aac -f null -
  ```

### PHASE B4 — Dual-Mono Audio Formatting & 48 kHz Alignment
- **Goal**: Align the genuine microphone audio track with the OBS audio contract:
  ```text
  Camera Microphone (Mono)
         ├──► Left Channel
         └──► Right Channel
  Sample Rate: 48,000 Hz
  Format: AAC-LC 128 kbps (or uncompressed PCM)
  ```

### PHASE B5 — Decoupling from MovieWriter & Wi-Fi Streaming
- **Goal**: Prevent the 14-second SD card buffer bottleneck by intercepting `task_MovieWriter` (`0xff37d5e0`), redirecting encoded H.264 and AAC packets to the Wi-Fi transmission queue, and acknowledging buffers without writing to SD card flash storage.

---

## 4. Hardware Execution Procedure Checklist

For running the Route B passive observation and validation sequence on hardware:

1. **Power & Battery**: Ensure the NB-11LH battery is 100% charged.
2. **SD Card Preparation**:
   - Write-protect switch: **LOCK** (for CHDK autoboot).
   - Ensure the CHDK build with enabled native calls (`CHDK ALT -> MENU -> Miscellaneous Stuff -> Enable Lua native calls`) is installed.
3. **Host PC Network Setup**:
   - Disconnect or pause any active VPNs (e.g., ProtonVPN) to avoid blocking local PTP/IP traffic on port 15740.
   - Run the native verification harness script on the PC (`RUN-NATIVE-AV.cmd` or PowerShell test harness).
4. **Camera Boot & Connection**:
   - Power on the camera in **Playback mode** (press Triangle button).
   - Open camera Wi-Fi menu and connect to the configured PC / Access Point (`SX430-PC`).
5. **Acoustic & Visual Test Scene**:
   - Point the camera at a distinct physical scene with visible movement (e.g. digital stopwatch / clock).
   - Make a clear audible sound (e.g. single sharp hand clap) within the first 2 seconds of the lens extending.
6. **Observation & Cleanup**:
   - Observe the live test execution; confirm `RESULT,FULL_FRAME_NATIVE_AV_PAYLOADS_TRANSFERRED`.
   - Wait for the camera to finish the bounded sample window, close recording, and return to Playback mode.
   - Power off the camera cleanly using the power button.
7. **Post-Flight Card Verification**:
   - Unlock the SD card write-protect switch and insert into the PC card reader.
   - Verify that the local reference movie (`MVI_xxxx.MP4`) and RAM payload dumps match bit-for-bit.
