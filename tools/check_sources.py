"""Verify included source excerpts; does not verify hardware or an external checkout."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'source-lock.json').read_text())
failed = []
for item in manifest['files']:
    path = (root / item['path']).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        failed.append(item['path'])
    elif hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        failed.append(item['path'])
print(json.dumps({'checked': len(manifest['files']), 'failed': failed,
                  'hardware_verified': False}, indent=2))
sys.exit(1 if failed else 0)
