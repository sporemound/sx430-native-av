# Wi-Fi protocol status

The implemented research path delegates PTP/IP to chdkptp. See
[PTP/IP notes](ptpip-notes.md) for discovery, transaction and format evidence, and
[Wi-Fi stack](wifi-stack.md) for firmware anchors.

No native A/V wire protocol is frozen. Before choosing native sockets or a CHDK
extension, complete coexistence, buffer-lifetime and throughput experiments. Required
logical fields are stream/codec identity, epoch, sequence, camera PTS, optional DTS,
access-unit boundary, configuration/discontinuity flags and bounded payload length.
The byte order, clock frequency, fragment size and packet-loss recovery contract
must be documented and tested together once the actual source is known.
