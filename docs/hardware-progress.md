# Sanitized research status

Private testing established firmware GM1.00B identity, matching upstream CRC blocks, ordinary CHDK startup, and stable shooting with Wi-Fi off. The hardware build used CHDK 1.7.0 revision 6357 alpha; the included research source snapshot is older and must not be treated as its exact source tree.

The modern chdkptp r1528 Windows PTP/IP client established playback communication. A longer playback session succeeded with camera ICMP reachability permitted; shorter sessions also completed without a firewall change. Packet capture has not established the precise timeout mechanism.

Shooting requests during Wi-Fi communication extended the lens and then returned to playback. Sampled connection states followed 12/8, then 15/9/2. The PC had not requested playback at the point of reversal. The playback-request flag at 0x2410 stayed set. A normal ModeDialToCamera event during the transition did not clear it.

An earlier offline diagnostic requested playback while already in playback and powered the camera off. The corrected diagnostic eliminated redundant requests and demonstrated offline shooting. An exported crash log belonged to a different session; it did not establish the cause of the short offline shutdowns.

A CHDK display packet transferred over Wi-Fi but contained no demonstrated live sensor image. No native encoded video or microphone stream was captured.

The direct-handler candidate in [mode-transition.md](mode-transition.md) has passed offline checks and remains untested on hardware. Native encoder access, AAC extraction, sustained throughput, timing, and OBS support remain unimplemented or unverified.

Raw logs, dates, device identifiers, network information, firmware dumps, and private provenance records are omitted. These are summarized observations, not public hardware acceptance evidence.
