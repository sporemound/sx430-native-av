# Sanitized research status

Private testing established firmware GM1.00B identity, matching upstream CRC blocks, ordinary CHDK startup, and stable shooting with Wi-Fi off. The hardware build used CHDK 1.7.0 revision 6357 alpha; the included research source snapshot is older and must not be treated as its exact source tree.

The modern chdkptp r1528 Windows PTP/IP client established playback communication. A longer playback session succeeded with camera ICMP reachability permitted; shorter sessions also completed without a firewall change. Packet capture has not established the precise timeout mechanism.

Shooting requests during Wi-Fi communication extended the lens and then returned to playback. Sampled connection states followed 12/8, then 15/9/2. The PC had not requested playback at the point of reversal. The playback-request flag at 0x2410 stayed set. A normal ModeDialToCamera event during the transition did not clear it.

An earlier offline diagnostic requested playback while already in playback and powered the camera off. The corrected diagnostic eliminated redundant requests and demonstrated offline shooting. An exported crash log belonged to a different session; it did not establish the cause of the short offline shutdowns.

An earlier CHDK display packet transferred over Wi-Fi without a demonstrated live scene. The later bounded trial below recovered changing preview images. No native encoded video or microphone stream was captured.

The corrected direct-handler candidate in [mode-transition.md](mode-transition.md) passed a short hardware trial. The two request flags changed as expected, followed by 50 consecutive samples agreeing on shooting across CHDK and both raw mode words. These samples span over five seconds. Deliberate cleanup returned the camera to playback, and the host received the complete log before disconnecting. Native encoder access, AAC extraction, sustained throughput, timing, and OBS support remain unimplemented or unverified.

The first candidate script attempt stopped at its first wait, before requesting shooting or invoking the native handler. Lua 5.1 rejected a yield across `pcall(run)`. The corrected script keeps waits outside protected calls and returns expected guard failures explicitly. A separate CSV defect expanded assert's error-message argument into the final column; memory reads now return exactly one numeric value. Real Lua 5.1 coroutine tests reproduce the original error and cover the correction.

During the successful trial the host waited for one camera-side script and received its log after cleanup. Independent PTP requests and live-frame retrieval while shooting were not measured. The short success therefore establishes a mode transition during an open session, not sustained native streaming.

Raw logs, dates, device identifiers, network information, firmware dumps, and private provenance records are omitted. These are summarized observations, not public hardware acceptance evidence.

## Four-frame transfer follow-up

A later bounded experiment retrieved four complete CHDK viewport packets between camera ready and acknowledgement messages. The camera confirmed shooting at both endpoints and in its intermediate samples, then returned to playback. The shooting capture window spanned about 1.86 seconds. Manual review of all four private grayscale previews showed a changing scene. Each packet contained 720 by 240 sampled luma values. This is display-preview data, not 1280 by 720 encoded movie output.

Each request took approximately 162–189 milliseconds, with deliberate pauses between requests. These timings do not establish sustained throughput or sensor frame rate. The complete log reached the host and the client exited successfully before the deliberate disconnection. Raw packets, images, logs, network details, and machine identifiers are excluded from this repository.

The next unresolved work is native encoder and microphone access, followed by synchronization, sustained transport, and OBS integration. The frame-transfer experiment is currently a private diagnostic; the public mode candidate remains the earlier short mode-only test.
