# Direct mode-handler candidate — short trial passed

The corrected candidate maintained shooting for 50 consecutive samples spanning over five seconds during an open PTP/IP session, then returned to playback deliberately. This is a short mode-transition result; independent PTP requests during shooting, live-frame delivery, sustained operation, and native video/audio streaming remain unverified.

Research experiment for SX430 IS firmware GM1.00B and CHDK revision 6357. Read [the limitations](../../docs/mode-transition.md) first. The template contains no firmware table and refuses to execute until generated from a locally verified dump.

From the repository root, with your own dump in the ignored `private/` directory:

```sh
python tools/generate_mode_candidate.py --rom private/PRIMARY.BIN
```

The generator checks firmware identity, both upstream CRCs, and the reviewed code-region digest. It creates `private/generated-candidate.lua` with 381 firmware words for runtime comparison. Keep the dump and generated script private.

Optional instruction checks require Unicorn 2.1.4 in your Python environment:

```sh
python tools/verify_mode_paths.py --rom private/PRIMARY.BIN
```

The report contains a digest of your input and belongs in `private/`.

## Hardware prerequisites and operation

- Charged camera with this exact firmware and CHDK build, verified ordinary boot/recovery, and working PTP/IP pairing.
- A separately obtained chdkptp r1528-compatible client. Historical `reference/chdkptp/` excerpts are not that runtime.
- **Enable Lua native calls** checked in CHDK's **Miscellaneous Stuff** menu. CHDK requires this camera-side choice; the script cannot enable it.
- Start in playback and leave ALT mode. Do not run the template from the SD script menu or press the shutter during the test.

From a connected chdkptp session whose working directory is this repository, use the client's `exec` command to execute this host-side Lua:

```lua
dofile('camera/experimental/run-mode.lua').run('private/generated-candidate.lua','private/native-mode.csv')
```

The runner makes one guarded attempt and closes the connection after its short result. A final camera Disconnected notification is expected and does not prove success. `STABLE_RECORD_OBSERVED` means at least 30 consecutive sampled shooting states, roughly three seconds. It is not a streaming acceptance result.

Turn CHDK native calls off after the experiment. Preserve private logs after a failure and review the cause before another trial. The camera also appends `WFNATIVE.CSV` to its card if logging starts. The public runner does not configure discovery, firewall rules, or a device address.
