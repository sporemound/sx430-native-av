# Experiment ledger

| ID | Experiment | State | Evidence / exit criterion |
| --- | --- | --- | --- |
| S01 | Inspect source and related ports | DONE, static only | source-lock.json, firmware-symbols.json, movie-pipeline.md |
| S02 | Offline tool tests | REPRODUCIBLE | tests/; artificial parser fixtures, not camera samples |
| H01 | Identify firmware and ordinary CHDK boot | OBSERVED PRIVATELY | hardware-progress.md; raw evidence excluded |
| H02 | PTP/IP viewport baseline | PARTIAL | packet transfer observed; changing live image not established |
| H03 | Exact-ROM movie/audio mapping | PARTIAL | mode-transition.md; encoder and audio buffer ownership unresolved |
| H04 | Normal local recording, passive samples | NOT RUN | valid camera H.264 and AAC samples with recorded provenance |
| H05 | Movie plus Wi-Fi coexistence | BLOCKED BY MODE REVERSAL | ordinary shooting reversed; direct-handler candidate untested |
| H06 | No SD readback; transport comparison | NOT RUN | identical source stream, measured sockets/PTP-IP comparison |
| H07 | Receiver and OBS | NOT RUN | both camera streams, preserved timing, no substitute devices |
| H08 | 30-minute acceptance | NOT RUN | sync, latency, loss, memory, thermal, stop/start evidence |

## H03 analysis setup

Verify the complete dump, then import raw ARM little-endian at its documented ROM
base into Ghidra. Use pinned CHDK `InitCHDKMemMap.py` before auto-analysis and
`ImportCHDKStubs.py` for the exact SX430 subdirectory. These scripts already handle
CHDK memory-map conventions; reuse them instead of creating another importer.
Check their language/runtime requirements against the installed Ghidra version.
The full scripts live in the pinned CHDK checkout obtainable with fetch_sources.py.

For each map entry, replace unknowns only with evidence: inputs, outputs, calling
convention, task context, buffer ownership, xrefs, identification method, confidence,
dump SHA-256 and observed behavior. Preserve competing interpretations.

## H04 first hook review

Trace queue producer, consumer and completion; prove a maximum size and validity
window. Review the exact hook site and continuation. First observe with networking
off during a normal local movie, retain normal SD writing and minimize copied data.
No arbitrary memory scanning on the live device. Disassemble only the owned dump
until the read region has a documented contract.

## H05 state matrix

Record playback/record mode, remote session type, UI state, movie request result,
encoder output observed, AAC output observed, PTP responsiveness, free memory and
temperatures. Start with unmodified firmware behavior. If rejected, trace the exact
condition and dependent allocations. Change one reviewed condition at a time only
after H03/H04 establish safety and recovery. Do not borrow another camera's branch patch.

## H08 final acceptance

At least 1800 seconds with native 1280×720/25 H.264 plus built-in microphone AAC-LC,
Wi-Fi only, no SD file round-trip. Measure initial and final A/V event offset and
maximum observed offset; require <50 ms drift and report absolute offset separately.
Measure camera-to-OBS latency with a synchronized visible event, initially <500 ms.
Log loss, reconnects, resynchronization after IDR, queue high-water bytes, battery,
temperature and repeated stop/start. A long recording or matching metadata alone
does not satisfy this test.
