#!/usr/bin/env python3
"""Run a finite chdkptp capture in a fresh evidence folder; no camera patches."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--chdkptp', type=Path, required=True)
    p.add_argument('--camera-ip', type=ipaddress.IPv4Address, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--count', type=int, default=300)
    p.add_argument('--wait-ms', type=int, default=0)
    p.add_argument('--timeout', type=int, default=180)
    a = p.parse_args()
    if not (1 <= a.count <= 10000 and 0 <= a.wait_ms <= 10000 and 1 <= a.timeout <= 3600):
        p.error('count 1..10000, wait-ms 0..10000, timeout 1..3600 required')
    exe = a.chdkptp.resolve(strict=True)
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(ROOT / 'camera/baseline.lua', out / 'capture.lua')
    env = os.environ.copy()
    lua_path = (exe.parent / 'lua/?.lua').as_posix()
    env['LUA_PATH'] = lua_path + ';' + env.get('LUA_PATH', ';')
    command = [str(exe), '-r', '-econnect -h=' + str(a.camera_ip),
               f"-eexec dofile('capture.lua').run({a.count},{a.wait_ms})"]
    start = time.monotonic()
    status = {'kind': 'viewport baseline', 'native_movie_verified': False,
              'audio_present': False, 'camera_ip': str(a.camera_ip), 'command': command,
              'completed': False}
    try:
        with (out / 'chdkptp.log').open('w', encoding='utf-8') as log:
            run = subprocess.run(command, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT,
                                 timeout=a.timeout)
        status['exit_code'] = run.returncode
        log_text = (out / 'chdkptp.log').read_text(encoding='utf-8', errors='replace')
        status['completed'] = run.returncode == 0 and 'SX430_BASELINE_COMPLETE;' in log_text
    except subprocess.TimeoutExpired:
        status['error'] = 'host capture deadline exceeded; camera state unverified'
    except OSError as e:
        status['error'] = str(e)
    status['host_wall_seconds'] = time.monotonic() - start
    (out / 'session.json').write_text(json.dumps(status, indent=2), encoding='utf-8')
    print(json.dumps(status, indent=2))
    return 0 if status['completed'] else 2


if __name__ == '__main__':
    sys.exit(main())
