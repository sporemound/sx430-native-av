# Build and reproduce

## Current research tools

Python 3.10+ and Git. The tools have no third-party Python imports; tests use unittest.
FFprobe is optional for original-sample metadata checks. chdkptp is an external
runtime required only for real camera baselines. No native receiver or camera image
is built by the current build script.

```powershell
./build.ps1
python tools/fetch_sources.py private/sx430-upstream
python tools/sx430.py import-map private/sx430-upstream/chdk
```

The fetch script requires network access and creates fresh directories. It checks
out immutable Git commits. Included evidence snapshots have a separate SHA-256
manifest checked by `tools/check_sources.py`. No downloaded source is automatically
built or executed.

Machine-specific environment records are excluded from the public snapshot.
No experimental ARM image or native streaming build has been validated. See
hardware-progress.md for the summarized ordinary CHDK and PTP/IP observations.

## Future firmware build

Obtain a supported CHDK ARM toolchain, keep its version and checksum, and use the
upstream build instructions for `PLATFORM=sx430is PLATFORMSUB=100b` at the pinned
revision. First reproduce the ordinary port and boot/recovery behavior. Experimental
hook integration is gated by recovery.md and exact-ROM analysis; simply uncommenting
the task hook would reference an absent implementation and is not a solution.

## Source pins

`dependencies.json` distinguishes source-inspected Git revisions from externally
published archive hashes and hardware validation. Obtain a verified modern client
before modifying its transport. Do not use the 2013 mirror as the shipping dependency.

## Optional mode checks

Install Unicorn 2.1.4 in an isolated Python environment for `tools/verify_mode_paths.py`.
It requires a locally supplied firmware dump; no firmware is downloaded by the tool.
The standard-library tests do not require Unicorn or a camera.

`tests/test_host_lua.lua` exercises the modern chdkptp return conventions and the
experimental host runner using mocks. Set `SX430_PROJECT_ROOT` to this repository's
path and run it with chdkptp's host `exec dofile(...)` from a fresh scratch directory.
It does not connect to a camera. Keep that scratch directory outside tracked source.

The optional `tests/test_camera_lua51.py` requires [Lupa](https://github.com/scoder/lupa)
with its `lupa.lua51` module. It explicitly uses Lua 5.1 rather than LuaJIT or a newer
Lua version. It runs 14 mocked camera scenarios with real coroutine yields,
checks CSV column counts, and reproduces the old protected-wait error. Tests are
skipped if that optional module is absent; inspect the test summary for skips.
