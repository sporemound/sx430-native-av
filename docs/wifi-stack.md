# Wi-Fi stack investigation

Upstream SX430 names:

- InitializeWLAN_FW: 0xff05c840
- ConnectPtpIPService_FW: 0xff178eb8
- task_PtpipController: 0xff178324
- task_PtpipPacketDetector: 0xff178878
- InitializePTPIPTransportResponder_FW: 0xff179ba0
- task_PTPSessionTASK: 0xff15a714

These functions are analysis anchors only. Socket entry points, parameter layouts,
thread restrictions and network-stack lifetime remain unknown. Do not call these
functions through CHDK native calls merely because their names sound useful.

Follow PtpipController and its socket users to discover the Canon network ABI;
correlate with known PTP/IP traffic before testing a transport worker. Find the
Wi-Fi initialization and shutdown owners and trace movie-start rejection in the
same exact firmware. No evidence yet distinguishes application policy from memory,
power, thermal or other resource conflicts.

Record a state matrix for normal playback, normal movie recording, computer pairing,
CHDK PTP/IP display reads, and any *reviewed* coexistence experiment. Preserve camera
errors and RAM allocation evidence. Compare changes to state, not just the UI label.
