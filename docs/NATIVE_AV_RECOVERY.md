# SX430 Native A/V Research Recovery

## Overview & Recovery Directive

This document establishes the evidence baseline and technical execution plan for discovering and verifying native audio and video boundaries on the Canon PowerShot SX430 IS (GM1.00B).

All statements, symbols, and findings in this document are strictly categorized with the following evidence taxonomy:
- `[HW-OBSERVED]`: Directly measured or observed during live hardware execution on the SX430 IS.
- `[ROM-VERIFIED]`: Statically disassembled and cross-referenced in the verified SX430 IS GM1.00B ROM dump (SHA256: `a67792b34e74a35ff93d7362e9bd1b6e2e3196cee471074d03e0a8fca1de031b`).
- `[UPSTREAM-SYMBOL]`: Derived from public CHDK / DryOS platform source trees and symbol tables.
- `[HOST-MOCK]`: Host-side synthetic processing, emulation, or transcoding running on the PC.
- `[HYPOTHESIS]`: Theoretical mechanism or architecture proposal awaiting hardware validation.

---

## A. Verified Facts

### 1. Hardware & Viewport Baseline
- `[HW-OBSERVED]` **CHDK Viewport Extraction**: The existing `con:live_get_frame_pcall(1)` and `liveimg.get_viewport_pimg()` paths retrieve uncompressed $720 \times 240$ YUV422 display framebuffer data (345,600 bytes per frame).
- `[HW-OBSERVED]` **Wi-Fi Viewport Throughput**: Transferring uncompressed display framebuffer memory over the camera's low-power 802.11n Wi-Fi interface yields approximately 2–5 frames per second due to TCP packet serialization over CHDK PTP.
- `[HW-OBSERVED]` **Visual Scene Change**: Bounded 4-frame diagnostic transfers confirmed changing real-world scenes in the $720 \times 240$ display framebuffer, confirming CHDK liveview operational continuity under Wi-Fi.
- `[HW-OBSERVED]` **Shooting Mode Transition**: The native mode transition handler operates while PTP/IP is connected; the camera extends its lens, sets internal shooting flags, and maintains shooting mode across multiple sample periods without triggering an unhandled exception.

### 2. ROM Firmware Architecture (GM1.00B, Platform 13013, DryOS R59)
- `[ROM-VERIFIED]` **Shooting Mode Switch Vector**: Vector `0xff05f154` called with registers `r0=0x105f`, `r1=0` writes `0x2410=0` and `0x2414=1`, transitioning the internal state machine (`pr=2, cc=1`) to active shooting mode.
- `[ROM-VERIFIED]` **Movie Start Entry Point**: `UIFS_StartMovieRecord_FW` is located at `0xff0687bc`, which initializes movie parameters and launches `task_MovieRecord` (`0xff1ecdbc`).
- `[ROM-VERIFIED]` **Movie Stop Entry Point**: `UIFS_StopMovieRecord_FW` is located at `0xff0687e0`.
- `[ROM-VERIFIED]` **Movie State Structure**: `MovieRecorder.c` initializes its state structure at RAM address `0x7bc0` (`0xff1ec698`), managing framerate settings at offset `+0x60` (supporting 10, 15, 20, 24, 25, 30, 60 fps).
- `[ROM-VERIFIED]` **Hardware Completion ISR Dispatch**: The video hardware completion ISR entry point `0xff1a9f84` reads the callback pointer from RAM address `0x7180` (base table `0x7150 + 0x30`), which defaults to `0xff33ae58`.
- `[ROM-VERIFIED]` **Asynchronous Video Descriptor Callback**: Registered at RAM address `0xc6c8`, with default handler `0xff1ec658`.
- `[ROM-VERIFIED]` **Movie Writer Message Queue**: `task_MovieWriter` (`0xff37c6dc`) receives video and audio message structures via function `0xff37d5e0` posted from `0xff1ecce8` (video frames) and `0xff1ed674`.
- `[ROM-VERIFIED]` **Audio / AAC Tasks**:
  - `task_AudioTsk`: `0xff075bbc` (microphone ADC and sound subsystem).
  - `task_AACTask`: `0xff18e4fc` (AAC audio encoder task).
  - `task_AACDrvTask`: `0xff3174b0` (AAC driver task).
  - AAC buffer descriptors are allocated via DryOS heap allocator `0xff027fc8` and referenced by `task_MovieWriter`.

### 3. Upstream Symbol Anchors
- `[UPSTREAM-SYMBOL]` `ConnectPtpIPService_FW` at `0xff178eb8`.
- `[UPSTREAM-SYMBOL]` `InitializePTPIPTransportResponder_FW` at `0xff179ba0`.
- `[UPSTREAM-SYMBOL]` `task_PtpipController` at `0xff178324`.
- `[UPSTREAM-SYMBOL]` `task_PtpipPacketDetector` at `0xff178878`.
- `[UPSTREAM-SYMBOL]` `task_PTPSessionTASK` at `0xff15a714`.
- `[UPSTREAM-SYMBOL]` `CreateMessageQueue` at `0xff039384`.
- `[UPSTREAM-SYMBOL]` `PostMessageQueue` at `0xff039650`.
- `[UPSTREAM-SYMBOL]` `ReceiveMessageQueue` at `0xff0394d4`.

---

## B. Unverified Claims Currently in Repo

The following claims previously present in experimental scripts, commits, or notes were investigated and identified as unverified or synthetic:

1. `[HOST-MOCK]` **"Native 720p @ 25 fps Video"**:
   - The FFmpeg filter pipeline `-vf fps=25,scale=1280:720` coupled with `libx264` was purely host-side upscaling, frame duplication, and host compression of $720 \times 240$ uncompressed display buffer grabs.
   - No native H.264 elementary stream or compressed video frames were retrieved from camera RAM.
2. `[HOST-MOCK]` **"Native Camera Microphone Audio"**:
   - The FFmpeg audio input `-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100` was synthetic host-generated silence.
   - No microphone PCM or AAC access units were extracted from the camera sound subsystem.
3. `[HYPOTHESIS]` **"14-Second SD Card FIFO Overflow"**:
   - The claim that recording over Wi-Fi causes a mandatory FIFO buffer overflow after exactly 14 seconds was an extrapolation from desktop network streaming limits and has not been confirmed on clean hardware recording logs.
4. `[HYPOTHESIS]` **"60–100 ms Native H.264 Latency" & "15–30 KB Frame Size"**:
   - Latency figures and encoded packet size estimates were theoretical projections based on DIGIC 4+ specifications, not measured packet round-trip times.
5. `[HYPOTHESIS]` **"DMA Bus Contention & WRITE_SD Failure"**:
   - Assertions that simultaneous Wi-Fi transmission and SD writes cause internal hardware DMA contention are unverified hypotheses.

---

## C. Canon Remote Live-View Packet Capture Results (Route A)

### 1. Protocol Architecture
- `[HYPOTHESIS]` **Stock Canon Camera Connect Streaming**:
  - The Canon PowerShot SX430 IS natively supports live-view preview streaming to the official Canon Camera Connect mobile application over standard 802.11n Wi-Fi.
  - This streaming operates continuously without writing movie files to the SD card and without triggering sensor shutdowns.
- `[ROM-VERIFIED]` **PTP/IP Stack Endpoints**:
  - PTP/IP transport responder initialized by `InitializePTPIPTransportResponder_FW` (`0xff179ba0`).
  - Network sessions serviced by `task_PtpipController` (`0xff178324`) and `task_PtpipPacketDetector` (`0xff178878`) on TCP port 15740.

### 2. Payload Framing Search Targets
When capturing live traffic between the camera and Canon Camera Connect, network packets must be inspected for the following signatures:
- `[HYPOTHESIS]` **JPEG / MJPEG Framing**:
  - SOI Marker: `0xFF 0xD8`
  - EOI Marker: `0xFF 0xD9`
  - Quantization / Huffman Tables: `0xFF 0xDB`, `0xFF 0xC4`, `0xFF 0xC0`
- `[HYPOTHESIS]` **H.264 / AVC Elementary Stream Framing**:
  - 3-byte / 4-byte Start Codes: `0x00 0x00 0x01` or `0x00 0x00 0x00 0x01`
  - NAL Unit Types:
    - SPS (Sequence Parameter Set): `0x67` (nal_unit_type = 7)
    - PPS (Picture Parameter Set): `0x68` (nal_unit_type = 8)
    - IDR Keyframe: `0x65` (nal_unit_type = 5)
    - Non-IDR Slice: `0x61` or `0x41` (nal_unit_type = 1)
- `[HYPOTHESIS]` **Canon PTP/IP Container Framing**:
  - Header: 4-byte packet length (little-endian), 4-byte packet type (`0x00000006` for Data Packet, `0x00000007` for Data End), followed by transaction ID and raw compressed payload.

### 3. Verification Protocol for Captured Frames
1. Capture raw TCP stream on port 15740 using `tshark` / `wireshark`.
2. Extract continuous payload segments; calculate SHA-256 hash.
3. Validate stream headers using native parsers:
   ```bash
   ffprobe -v error -show_format -show_streams candidate_stream.bin
   ```
4. Verify that decoded images accurately reflect the live physical scene in front of the lens.

---

## D. `task_MovieRecord` Call Graph (Route B Video Producer)

```
UIFS_StartMovieRecord_FW (0xff0687bc)
  │
  └──> task_MovieRecord (0xff1ecdbc)
         │
         ├──> State Initialization (0xff1ec698)
         │      ├── Load State Struct: 0x7bc0
         │      ├── Configure Framerate: [0x7bc0 + 0x60] (10/15/20/24/25/30/60 fps)
         │      ├── Setup MovieWriter Helper: 0xff37b538
         │      ├── Register Properties: 0xff0aeb34 (IDs: 0xb2, 0xb1, 0xab, 0xac)
         │      └── Timer Config: 0xff035288
         │
         ├──> MovieWriter Track Configuration
         │      ├── Buffer Registration: 0xff37c8ec
         │      ├── Track Parameters: 0xff37cedc
         │      └── Stream Config: 0xff37b2fc
         │
         ├──> Video Encoder Hardware Callback Registration
         │      ├── Mode check (r1 == 2 vs other)
         │      ├── Handler Dispatch Setup: 0xff33af30 / 0xff338d98
         │      ├── Register Async Callback: 0xff33b454 (0xff1ec658) / 0xff3393d0 (0xff1ec64c)
         │      └── Hardware ISR Vector Table: 0xff1aa26c -> Table 0x7150 (Callback slot 0x7180)
         │
         ├──> Audio Capture Link
         │      ├── Query Audio Buffers: 0xff37d164
         │      └── Hook Audio Subsystem: 0xff078828 -> task_AudioTsk (0xff075bbc)
         │
         └──> Video Frame Enqueue (Live Loop)
                ├── Encode Completion ISR: 0xff1a9f84 -> ldr pc, [0x7180]
                ├── Descriptor Dispatch: 0xff1ecce8 -> bl #0xff37d5e0 (Post to MovieWriter queue)
                └── Secondary Dispatch: 0xff1ed674 -> bl #0xff37d5e0
```

- `[ROM-VERIFIED]` **Key Observation**: Video frames are completed by the hardware encoder, signaled via ISR at `0x7180`, formatted into descriptor `[sp, #0x4c], [sp, #0x54]`, and enqueued to `task_MovieWriter` via `0xff37d5e0`.

---

## E. `task_MovieWriter` Call Graph (Route B Consumer / Muxer)

```
task_MovieWriter (0xff37c6dc)
  │
  ├──> Message Queue Listener (0xff37d5e0)
  │      ├── Receives Video Descriptors from task_MovieRecord (0xff1ecce8)
  │      └── Receives Audio Descriptors from task_AACTask (0xff18e4fc)
  │
  ├──> MP4 Container & Chunk Muxer (0xff37d2b0 - 0xff37d360)
  │      ├── String Anchor: 0xff37c530 ("MovieWriter.c")
  │      ├── Offset & Sample Indexing: 0xff37d2bc ([r4, #0x38])
  │      ├── Buffer Overflow Check: 0xff37d2dc (cmp r0, #0xa -> error 0xff025500)
  │      └── Track Interleave Calculator: 0xff37d308 (mul r1, r2, r1)
  │
  └──> SD Storage Write Pipeline
         └── Dispatches container blocks to task_FileWrite (0xff35dd00)
```

- `[ROM-VERIFIED]` **Decoupling Boundary**: `task_MovieWriter` is the single point where video and audio descriptors converge before MP4 box formatting and disk I/O. Intercepting `0xff37d5e0` or hooking the completion ISR at `0x7180` allows extracting native encoded buffers before disk serialization.

---

## F. Audio & AAC Task Call Graph

```
Microphone Hardware ADC
  │
  ▼
task_AudioTsk (0xff075bbc)
  │
  ├── DMA Buffer Capture
  └── Triggered by Movie Hook: 0xff078828 (called from MovieRecorder.c 0xff1ec8b8)
        │
        ▼
task_AACDrvTask (0xff3174b0) / task_AACTask (0xff18e4fc)
  │
  ├── Memory Allocation: DryOS Malloc 0xff027fc8 (Descriptor Pool)
  ├── AAC-LC Compression Engine
  └── Audio Frame Dispatch:
        └── Enqueue Audio Descriptor to task_MovieWriter (0xff37d164 / 0xff37d5e0)
```

- `[ROM-VERIFIED]` **Audio Subsystem Verification**:
  - `task_AudioTsk` at `0xff075bbc` handles raw PCM capture from internal stereo/mono microphone hardware.
  - `task_AACTask` at `0xff18e4fc` and `task_AACDrvTask` at `0xff3174b0` compress PCM audio into AAC access units.
  - Audio buffer pointers are queried via `0xff37d164` and fed to `task_MovieWriter`.

---

## G. Next Single Hardware Experiment

### Experiment Title: Stock Canon Camera Connect Wi-Fi Packet Capture & Frame Extraction (Route A)

### Objective
Capture and reconstruct one genuine, camera-origin compressed video frame (JPEG or H.264) directly from the stock Canon Wi-Fi live-view transmission to Canon Camera Connect, without firmware modification.

### Experimental Setup
1. **Network Configuration**:
   - Set up an isolated 802.11n 2.4 GHz Wi-Fi Access Point (or host PC mobile hotspot).
   - Connect Canon PowerShot SX430 IS to the Access Point.
   - Connect mobile phone (or Android emulator running Canon Camera Connect) to the same Access Point.
2. **Packet Capture Probe**:
   - Run `tshark` or `wireshark` on the host machine monitoring all traffic between the camera IP and mobile device IP.
   - Filter on PTP/IP traffic: `tcp.port == 15740`.

### Execution Steps
1. Launch Canon Camera Connect and initiate "Remote Live View Shooting".
2. Record complete packet trace (`canon_liveview_stock.pcapng`) for 10 seconds of active live scene motion.
3. Stop capture and disconnect session cleanly.

### Analysis & Decoding Protocol
1. Filter the TCP stream for PTP/IP Data packets (`type == 0x00000006`).
2. Search payload bytes for image start markers:
   - JPEG: `0xFF 0xD8`
   - H.264: `0x00 0x00 0x01` / `0x00 0x00 0x00 0x01`
3. Extract candidate frame payload into `test_extracted_frame.bin`.
4. Validate frame headers and decode with standard open-source tools:
   ```bash
   ffprobe -v error -show_format -show_streams test_extracted_frame.bin
   ffmpeg -v error -i test_extracted_frame.bin -f null -
   ```

### Pass / Fail Success Criteria
- **PASS**: `ffprobe` / `ffmpeg` parses the extracted byte payload as a valid compressed image/frame without errors, and the decoded visual matches the physical scene recorded during the test.
- **FAIL**: Payload contains only raw display buffer pixels, uncompressed YUV data, corrupted stream headers, or requires host-side format reconstruction.
