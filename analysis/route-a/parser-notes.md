# Route A PTP/IP Protocol & Framing Specification

## 1. PTP/IP Packet Layer & Header Specification

All PTP/IP transactions on TCP port 15740 conform to standard PIMA 15740 / ISO 15740 framing over TCP.
Every PTP/IP packet begins with an 8-byte header:

```text
Offset  Type     Field
0x00    uint32   packet_length (little-endian, total packet bytes including header)
0x04    uint32   packet_type   (little-endian)
```

### Standard Packet Type Table
| Type Code | Symbolic Name | Data Phase / Direction | Description |
|---|---|---|---|
| `0x00000001` | `Init_Command_Request` | Client -> Camera | Initiates command channel connection with client GUID. |
| `0x00000002` | `Init_Command_Ack` | Camera -> Client | Confirms command channel; assigns Connection ID. |
| `0x00000003` | `Init_Event_Request` | Client -> Camera | Initiates asynchronous event channel using Connection ID. |
| `0x00000004` | `Init_Event_Ack` | Camera -> Client | Confirms event channel readiness. |
| `0x00000005` | `Init_Fail` | Camera -> Client | Handshake rejection. |
| `0x00000006` | `Operation_Request_Packet` | Client -> Camera | Requests operation (Opcode, Transaction ID, Parameters). |
| `0x00000007` | `Operation_Response_Packet` | Camera -> Client | Returns operation status (Response Code, Transaction ID). |
| `0x00000008` | `Event_Packet` | Camera -> Client | Asynchronous notification (Event Code, Transaction ID). |
| `0x00000009` | `Start_Data_Packet` | Sender -> Receiver | Initiates data phase; declares 64-bit total payload length. |
| `0x0000000A` | `Data_Packet` | Sender -> Receiver | Carries intermediate chunk of payload bytes. |
| `0x0000000B` | `Cancel_Packet` | Sender -> Receiver | Cancels active data phase. |
| `0x0000000C` | `End_Data_Packet` | Sender -> Receiver | Carries final chunk of payload bytes, completing data phase. |
| `0x0000000D` | `Probe_Request_Packet` | Either -> Other | Keepalive Ping. |
| `0x0000000E` | `Probe_Response_Packet` | Either -> Other | Keepalive Pong. |

---

## 2. Stream Reassembly & Framing Rules

PTP/IP payload extraction requires continuous TCP byte-stream reconstruction. Individual TCP segment boundaries must not be treated as packet or frame boundaries.

```text
TCP Stream
   │
   ├──> PTP/IP Packet Layer:
   │      [length: 4B][type: 4B][TransactionID: 4B][Payload...]
   │
   └──> Multi-Packet Data Assembly:
          StartData (0x09) ──> Data Chunk 1 (0x0A) ──> ... ──> EndData (0x0C)
                                                                    │
                                                                    ▼
                                                       Reconstructed Application
                                                       Payload Buffer
```

---

## 3. Canon Live-View Operation Framing (`0x9052`)

When Canon Camera Connect requests live viewfinder frames using vendor operation `0x9052` (`CanonGetLiveViewPicture`), the camera returns a structured application payload:

```text
+-------------------------------------------------------------------------------+
| Canon Viewfinder Metadata Header (128 bytes)                                  |
|   - 0x00..0x03: Total Header Size (0x00000080 = 128 bytes)                     |
|   - 0x04..0x07: Total Payload Size (including header)                         |
|   - 0x08..0x0B: Frame Sequence Counter                                        |
|   - 0x0C..0x0F: Image Width  (0x00000280 = 640)                              |
|   - 0x10..0x13: Image Height (0x000001E0 = 480)                              |
|   - 0x14..0x17: Focus & Exposure State Flags                                  |
|   - 0x18..0x7F: AF Box Coordinates, Histogram Data, Zoom Position             |
+-------------------------------------------------------------------------------+
| Compressed JPEG Stream (SOI to EOI)                                           |
|   - Offset +128: 0xFF 0xD8 (JPEG SOI Marker)                                  |
|   - JFIF / EXIF APP markers, Quantization Tables, Huffman Tables              |
|   - JPEG Encoded Viewfinder Scan Lines                                        |
|   - Final 2 bytes: 0xFF 0xD9 (JPEG EOI Marker)                                |
+-------------------------------------------------------------------------------+
```

### Key Framing Observations
1. **Header Offset**: The JPEG stream begins at exact byte offset `+128` (`0x80`) within the reconstructed PTP/IP data payload.
2. **Format**: Standard JFIF baseline JPEG at $640 \times 480$ resolution.
3. **Absence of H.264**: Zero H.264 Annex B start codes (`00 00 01` / `00 00 00 01`) or AVCC length-prefixed NAL units are present anywhere in the payload.
4. **Cadence**: Requests are driven by client polling at ~10–15 Hz (~75 ms inter-request spacing).

---

## 4. Audio Traffic Analysis on Route A

Analysis of all TCP and UDP streams across the entire Canon Camera Connect session confirmed:
- **Zero Audio Packets**: PTP/IP command and data channels carry only property queries, event polls, and `0x9052` image payloads.
- **No Sideband Audio Channels**: No RTP, RTSP, UDP audio datagrams, or secondary TCP audio sockets exist.
- **Classification**: `ROUTE A VIDEO ONLY`. Microphone audio is not exposed via the stock Canon PTP/IP remote-view protocol.
