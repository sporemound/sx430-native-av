# Receiver status

The only implemented host acquisition path is the finite **viewport baseline** in
`tools/capture_baseline.py`, delegating PTP/IP to upstream chdkptp. Offline parsers
live in `tools/sx430.py`. They do not acquire native video or microphone samples.

Build the native headless Rust or C++ receiver after the encoded-buffer and transport
contracts are verified. Reuse chdkptp's proven pairing/session handling where practical.
The receiver will preserve camera timestamps, handle configuration/reconnect epochs,
reassemble bounded access units and remux through FFmpeg. No untested custom UDP,
PTP extension or fake source is included to stand in for unavailable camera data.
