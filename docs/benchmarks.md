# Measurements

No hardware measurements exist. All target values are requirements, not results.

| Quantity | Result | Method |
| --- | --- | --- |
| Viewport dimensions | not measured | live protocol descriptor + visual validation |
| Retrieval throughput | not measured | payload bytes / host capture duration |
| Camera frame rate | not measured | source timestamps/sequence or independent observation |
| PTP request duration | not measured | before/after host timestamps, p50/p95 |
| One-way network latency | not measured | synchronized clocks or bounded clock estimation |
| Camera→OBS latency | not measured | physical event seen at both endpoints |
| Video/audio bitrate | not measured | encoded byte counters per camera time interval |
| Packet loss | not measured | transport sequence evidence, not TCP read count |
| Dropped frames | not measured | encoder/queue/receiver counters kept separate |
| A/V drift | not measured | visible/audible events at start and end |
| CPU/memory | not measured | host process counters and reviewed camera instrumentation |
| Temperature/battery | not measured | calibrated getter logs over real elapsed time |

The live dump lacks acquisition timestamps and frame sequence IDs. Repeated display
retrieval can return the same sensor frame; identical bytes can also be a static scene.
The parser deliberately does not call either case a dropped or unique frame.
Host request duration includes network and camera service. Do not call it camera-to-OBS
latency or derive one-way latency by halving it without a justified model.

`telemetry.txt` logs battery/sensor/optical readings and millivolts before/after capture.
Missing, implausible or error readings are unavailable. Battery voltage change is
not a calibrated state-of-charge or battery-drain measurement.
