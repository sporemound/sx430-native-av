# First camera session

No SD card has been altered and no CHDK image has been built by this project.

1. Preserve any existing SD contents. Determine the installed **Canon** firmware
   through the supported camera/version-identification procedure, such as an original
   photo's firmware metadata with a CHDK-supported identifier. A model name or CHDK
   build name alone is insufficient. Record the full result and method.
2. Obtain a build explicitly for **sx430is / 100b** from CHDK's maintained distribution.
   Check its provenance and follow the model-specific SD boot procedure. The source
   requires encoded DISKBOOT type 17; an arbitrary ARM binary cannot be used as-is.
3. Establish the recovery procedure in recovery.md before any experiment. Boot the
   ordinary CHDK build from SD, verify expected power/playback behavior, then verify
   return to stock operation with a non-CHDK card. Do not change internal Canon firmware.
4. If USB diagnostics are necessary, use the appropriate chdkptp USB driver only for
   the camera device. No USB hardware change is automated here. USB is optional for
   baseline investigation and must be absent from final streaming acceptance.
5. Obtain a recent chdkptp Windows PTP/IP build. Confirm it accepts `connect -h=...`.
   Keep its supplied libraries and Lua files. See dependency manifest for a published
   r1528 archive hash; that archive was not retrieved or tested here.
6. Pair using the pinned helper or Windows' supported discovery responses. Run the
   helper in the foreground for this initial diagnostic so logs and camera selection
   are visible. Preserve its UUID. Do not run a camera control app concurrently.
7. Connect chdkptp to the actual camera IPv4 address. Read `get_buildinfo()`. Use its
   normal live-view UI to demonstrate a real display feed, then run our bounded capture.

Baseline output: `identity.txt`, `telemetry.txt`, `baseline.lvdump`, `timing.csv`,
`chdkptp.log`, `session.json`. It contains display data only. A camera in playback
may provide a blank/unavailable or non-live viewport; record mode and confirm actual
scene changes visually. Successful protocol retrieval is not proof of fresh imagery.

The launcher refuses an existing output folder and stops its child process after its
deadline. It does not start recording, unlock the UI, change shooting mode, read
arbitrary addresses or write camera files. The chdkptp connection itself may perform
its upstream initialization; retain the client's configuration and revision as evidence.
