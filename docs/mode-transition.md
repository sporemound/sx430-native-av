# Wi-Fi shooting-mode investigation

| Address | Interpretation supported by inspected code |
| --- | --- |
| 0x3ac8 | Playback/record word; stable shooting observed as 2 |
| 0x23cc | CameraCon state; stable shooting observed as 1 |
| 0x2410 | Playback-request flag; set throughout failed Wi-Fi trials |
| 0x2414 | Adjacent camera-request flag |
| 0x28d4 | Wireless-controller-related word; exact meaning unresolved |

The shooting-entry handler reads 0x2410 at 0xff06006c. If nonzero, it can call Rec2PB(-1). With the flag clear, USB-control-event handling provides another possible return path. Sampled state is consistent with this branch but does not prove which call executed on the camera.

## Bounded instruction findings

The optional `tools/verify_mode_paths.py` executes selected ARM paths using Unicorn 2.1.4 and locally verified firmware. It initializes RAM from the firmware copy plus explicit synthetic state. Every executed address is checked. Application-callback checks stop at the CameraCon boundary without inventing external function return values.

Seventeen cases established:

1. Queue filter 0xff202fd0 returns zero for event 0x105f with either value of its flag at 0x8630. That specific filter does not explain rejection.
2. Application callback 0xff02a7e8, with its shutdown flag clear, replaces mode-dial events 0x1051 through 0x10a2 with 0xffffffff before the CameraCon call. The live callback order was not recorded, so this is a plausible explanation for the ineffective posted event.
3. Pre-handler 0xff05f154 with r0=0x105f and r1=0 writes 0x2410=0 and 0x2414=1 outside its stack, calling no other function along that path. Tests cover states 2, 8, 12, and 15 and both initial flag values. Its return register is not a success result.

## Candidate boundary

The generated candidate requests normal PTP shooting once and calls that handler once only if the raw transition matches playrec=3/CameraCon=12 or playrec=1/CameraCon=8 with the playback flag set. It checks model, firmware code, CHDK revision, native-call permission, and battery first. It verifies both flag writes, observes mode state, and requests normal playback only if both raw words agree on shooting.

The experiment changes RAM through a native routine. It is not a persistent firmware patch and does not start movie recording. Concurrent scheduling, further Wi-Fi restrictions, and sustained shooting are not modeled. Stable shooting, if later observed, would still not demonstrate native video or microphone transport.

Private candidate preparation passed 17 ARM checks, 14 camera-script host simulations, and 6 host-runner simulations. Host simulations used mocks. The public export provides standard-library tests and optional firmware-driven checks; it excludes the private ROM and raw execution report.
