# Firmware symbol map

All entries below are **source-derived anchors**, not independently verified live firmware findings.
An owner dump has now been supplied and matches the SX430 1.00B fingerprint;
see hardware-progress.md. The entries below still require independent analysis
of that dump before calling or patching their addresses.

The machine-readable [symbol ledger](firmware-symbols.json) records address, probable name,
calling convention, inputs/outputs, ownership, task, cross-references, confidence and identification method.
Unknown contracts and empty cross-reference lists are intentional. Source lines are provenance,
not firmware code cross-references. Some function names are aliases for the same address.

| Address | Probable symbol | Evidence |
| --- | --- | --- |
| 0xff1585fc | `add_ptp_handler` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L36) |
| 0xff178eb8 | `ConnectPtpIPService_FW` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L181) |
| 0xff039384 | `CreateMessageQueue` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L206) |
| 0xff0790cc | `GetBatteryTemperature` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L470) |
| 0xff079058 | `GetCCDTemperature` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L477) |
| 0xff023548 | `GetMemInfo` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L702) |
| 0xff079140 | `GetOpticalTemperature` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L721) |
| 0xff028338 | `GiveSemaphore` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L799) |
| 0xff179ba0 | `InitializePTPIPTransportResponder_FW` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L924) |
| 0xff05c840 | `InitializeWLAN_FW` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L928) |
| 0xff039650 | `PostMessageQueue` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L1427) |
| 0xff0394d4 | `ReceiveMessageQueue` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L1481) |
| 0xff028254 | `TakeSemaphore` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L1983) |
| 0xff3174b0 | `task_AACDrvTask` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L1989) |
| 0xff18e4fc | `task_AACTask` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L1990) |
| 0xff075bbc | `task_AudioTsk` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L1995) |
| 0xff35dd00 | `task_FileWrite` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L2039) |
| 0xff35dd00 | `task_FileWriteTask` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L2040) |
| 0xff1ecdbc | `task_MovieRecord` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L2080) |
| 0xff37c6dc | `task_MovieWriter` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L2081) |
| 0xff178324 | `task_PtpipController` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L2090) |
| 0xff178878 | `task_PtpipPacketDetector` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L2091) |
| 0xff15a714 | `task_PTPSessionTASK` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L2092) |
| 0xff039714 | `TryPostMessageQueue` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L2142) |
| 0xff0687bc | `UIFS_StartMovieRecord_FW` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L2202) |
| 0xff0687e0 | `UIFS_StopMovieRecord_FW` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/funcs_by_name.csv#L2203) |
| 0x00007c0c | `movie_status` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/stubs_entry.S#L49) |
| 0x00007bbc | `video_compression_rate` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/stubs_entry.S#L50) |
| 0x000023cc | `cameracon_state` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/stubs_entry.S#L69) |
| 0x00001fdc | `imager_active` | [upstream](https://github.com/petabyt/chdk/blob/ad402e1b2049662594ccc7d15a9a507138b59079/trunk/platform/sx430is/sub/100b/stubs_entry.S#L67) |

## Still unresolved

Sensor input, H.264 output, PCM and AAC output descriptors; codec configuration; A/V clock;
muxer inputs; ADC/DMA ownership; network socket ABI; movie/Wi-Fi exclusion condition.
Task names identify where to investigate, not completed traces through those subsystems.

Use upstream Ghidra memory-map/stub import tools with the exact dump. Keep all analysis
associated with the dump SHA-256, not only the claimed firmware version.
