# Architecture and evidence gates

## Intended data path

Camera sensor → native H.264 output and camera microphone → native AAC output
→ bounded camera-owned copies → transport worker → host receiver → timestamp-preserving
remux → OBS. Encoder callbacks must never wait for network or host activity.

No encoded buffers, buffer ownership contract, or common A/V timebase have been
verified. This diagram is the target, not an implemented data path.

## Decision 001: reuse upstream PTP/IP for the baseline

The upstream helpers implement Canon discovery/pairing, and chdkptp already implements
CHDK transactions and display capture. Reimplementing these before proving the camera
connection would add uncertainty. The current Python launcher orchestrates chdkptp;
it is a research tool, not the requested final Rust/C++ native receiver.

## Decision 002: defer a new camera transport

Native sockets are preferred only after exact-ROM ABI, execution context, and initialized
network lifetime are known. Batched CHDK PTP/IP is the alternative. Neither has been
benchmarked with movie data. No private opcode numbers have been assigned and no
parallel transports have been built. Proposed AVStream names are not existing CHDK APIs.

Compare both using the same *camera-produced* access units and timestamps, reporting
CPU/task time, achievable throughput, p95/p99 service time, and memory. First test
whether an existing PTP session survives a normal local movie start. A failed UI
start is a clue to trace, not proof of a hardware conflict.

## Data contracts to establish before implementation

- Video: Annex B versus length-prefixed AVC, access-unit boundary, SPS/PPS lifetime,
  IDR indication, encoder clock and whether DTS differs from PTS.
- Audio: raw AAC access units versus ADTS, AudioSpecificConfig, sample rate, channel
  count, samples per access unit and relationship to the video clock. Do not assume
  ADTS framing or that timestamps equal host arrival times.
- Ownership: callback validity interval, producer recycle/ack, cached/uncached alias,
  maximum size, fragmentation, task context and reentrancy.
- Loss: whole-access-unit drop, explicit discontinuity, suppress dependent H.264
  pictures until a valid random access point, repeat codec configuration as required.
  Do not reset only one stream's epoch or silently synthesize missing audio.
- Flow: bound bytes and access units, not just packet count. A host stall must never
  block Canon's writer. Existing references cannot be retained beyond proven lifetime.

## OBS integration gate

Evaluate a dedicated OBS source after extraction succeeds. A timestamp-preserving
FFmpeg MPEG-TS output to localhost is the smaller interoperability milestone. Neither
is implemented; there is no reason to choose a final container or plugin before the
encoder output format is known. H.264 decoding/re-encoding is not part of the plan.
