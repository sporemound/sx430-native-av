# Route B Native Hardware Encoder & Microphone Extraction Results

## 1. Executive Summary & Proof Gate Validation

Pursuant to the **SX430 Native A/V — Research Recovery Directive** and **Route B Execution Directive**, this report documents the empirical hardware validation of native camera-origin video and audio boundaries on the Canon PowerShot SX430 IS (GM1.00B).

### Major Milestone Gates Achieved
1. **`[HW-OBSERVED]` Native H.264 Video Boundary (Phase B2)**:
   - Extracted 1 full-frame native H.264 video payload (**77,368 bytes**, NAL type 1, slice) directly from DIGIC 4+ hardware encoder ring buffer address `0x483A26FC` via Wi-Fi during active movie recording.
   - **Bit-Exact Verification**: Compared against the saved SD card movie (`MVI_1308.MP4`), the extracted 77,368-byte payload matched **Video Packet #2 (PTS 0.080000s)** bit-for-bit (100% exact byte match).
   - **Resolution & Frame Rate**: $1280 \times 720$ progressive, Constrained Baseline, `pix_fmt=yuvj420p`, $25.000$ fps hardware timebase (`1/25000`).

2. **`[HW-OBSERVED]` Native Microphone Audio Boundary (Phase B3 & B4)**:
   - Extracted 3 contiguous AAC audio batches totaling **67 frames (22,870 bytes)** directly from `task_AACTask` descriptor memory.
   - **Contiguity & Zero Gaps**: Audio packet matching against `MVI_1308.MP4` confirmed **zero gaps `[0, 0]`** across all 3 batches, spanning $1.429$ seconds of contiguous audio.
   - **Acoustic Event Verification**: Decoded PCM signal confirmed non-zero acoustic waveform with a sharp physical transient peak of **8,106 amplitude** (user hand clap), proving genuine built-in microphone origin.
   - **Format**: AAC-LC at **48,000 Hz** in dual-channel container.

3. **`[HW-OBSERVED]` Clean Lifecycle & Wi-Fi Coexistence**:
   - Encoder ISR callback (`0x7180`) and AAC descriptor hooks operated concurrently with 802.11n Wi-Fi transfer without triggering an unhandled exception or firmware freeze.
   - The camera cleanly returned to Playback mode (`pr=3, cc=2`) with `DONE` and powered off normally.

---

## 2. Evidence Taxonomy & Tagged Measurements

| Item | Tag | Exact Value / Address | Verification Method |
|---|---|---|---|
| **Video Payload Size** | `[HW-OBSERVED]` | 77,368 bytes (NAL type 1) | Bit-exact match to MP4 Packet #2 |
| **Encoder Ring Address** | `[ROM-VERIFIED]` | `0x483A26FC` (Ring: `0x4836B9F0`..`0x4FD59270`) | RAM descriptor query |
| **Video Dimensions** | `[HW-OBSERVED]` | $1280 \times 720$ | SPS / MP4 header inspection |
| **Video Frame Rate** | `[HW-OBSERVED]` | 25.000 fps (`time_base=1/25000`) | Hardware timebase probe |
| **Audio Frame Count** | `[HW-OBSERVED]` | 67 AAC frames (3 batches) | Bit-exact match to MP4 Packets 0..66 |
| **Audio Sample Rate** | `[HW-OBSERVED]` | 48,000 Hz | AAC ADTS / ASC header probe |
| **Audio Contiguity** | `[HW-OBSERVED]` | 0 gap packets between batches | Packet sequence alignment |
| **Acoustic Transient Peak**| `[HW-OBSERVED]` | 8,106 PCM amplitude (Hand Clap) | Decoded 16-bit PCM waveform analysis |

---

## 3. Detailed Hardware Run Data (`native-av-13`)

### A. Video Payload Descriptor Record
```json
{
  "described_video_bytes": 77368,
  "payload_bytes": 77368,
  "allocation_address": 1078869984,
  "source_address": 1211774716,
  "ring_start": 1211550192,
  "ring_end": 1339017712,
  "writer_frame_index_zero_based": 2,
  "nal_type": 1,
  "wrapped": false,
  "prefix_normalization_bytes": 4,
  "armed_tick_ms": 45500,
  "ready_tick_ms": 45600,
  "ack_tick_ms": 45700
}
```

### B. Audio Batches & Signal Analysis Record
```json
{
  "batches": 3,
  "aac_frames_matched": 67,
  "aac_payload_bytes_matched": 22870,
  "gap_packets_between_batches": [0, 0],
  "captured_interval_contiguous": true,
  "captured_encoded_duration_seconds": 1.429333,
  "audio_signal": {
    "decoded_samples_per_channel": 68608,
    "nonzero_signal_present": true,
    "rms_per_channel": [1148.01, 1148.01],
    "peak_per_channel": [8106, 8106]
  }
}
```

---

## 4. Next Step: Phase C (Continuous Wi-Fi Transport & SD Decoupling)

Now that both **Native Video (Phase B2)** and **Native Audio (Phase B3/B4)** are proven on hardware with bit-exact validation:

1. **SD Write Decoupling**:
   - Discard container write dispatch at `task_MovieWriter` (`0xff37d5e0` / `0xff35dd00`) to prevent SD card writing while streaming.
2. **Continuous Ring Transport**:
   - Stream successive H.264 NAL units and AAC access units over a non-blocking TCP / PTP/IP batched queue.
3. **OBS Media Source Ingestion (Phase D)**:
   - Package extracted native H.264 ($1280 \times 720$ @ 25 fps) + 48 kHz dual-mono AAC into standard timestamp-aligned MPEG-TS stream for direct OBS ingestion.
