# PTP/IP baseline

The [upstream pairing helper](https://github.com/reyalpchdk/ptpip-canon-helpers)
answers SSDP discovery and description requests. It is not a PTP client. Its
persistent UUID must remain stable across pairing and later sessions. Run it from
a dedicated local folder, passing this PC's reachable LAN IPv4 address. The camera
must select the advertised computer in its own connection menu.

The helper listens for SSDP on UDP 1900 and serves the description on TCP 8043 by
default. PTP/IP uses TCP 15740 on the camera. Do not disable Windows Firewall globally;
if needed, allow the relevant application on the local private network.

The helper warns that shooting-mode access can fail on some cameras. That statement
does not establish SX430 behavior. Its manual keepalive/UI-unlock instructions and
chdkptp's automatic equivalents must be evaluated as part of the baseline, not treated
as a general movie-start bypass.

[chdkptp r1528 announcement](https://chdk.setepontos.com/d/14874-chdkptp-alternative-ptp-client-release-10-rc1)
documents Windows builds with the `-ptpip` suffix. It also says host Lua is 5.3.
The project could not retrieve the modern source through the upstream Subversion
endpoint (HTTP 401). The available 2013 mirror was inspected only for the dump
format and public Lua methods. It must not be presented as a working modern client.

## Protocol reuse

CHDK opcode `0x9999`, parameter 1 `12` is GetDisplayData in the inspected `core/ptp.h`.
Its display subprotocol is separate from CHDK's main protocol version. The parser
accepts dump format 1.0 and live protocol major 2, with the SX430 YUV8 viewport.
Unknown types and out-of-bounds descriptors are rejected, not guessed.

The native AVStream commands in the project brief are proposals only. A future
extension needs capability negotiation, assigned command IDs, a bounded batch size,
timeouts and explicit discontinuities. Existing still-image remote capture is not
evidence of native movie or microphone capture.
