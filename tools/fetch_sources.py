"""Fetch pinned public Git sources into fresh directories; never execute upstream code."""
import argparse
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('destination', type=Path)
a = p.parse_args()
config = json.loads((root / 'dependencies.json').read_text())
a.destination.mkdir(parents=True, exist_ok=False)
for item in config['git_sources']:
    dest = a.destination.resolve() / item['name']
    subprocess.run(['git', 'init', str(dest)], check=True)
    subprocess.run(['git', '-C', str(dest), 'remote', 'add', 'origin', item['url']], check=True)
    subprocess.run(['git', '-C', str(dest), 'fetch', '--depth', '1', 'origin', item['commit']], check=True)
    if item['name'] == 'chdk':
        subprocess.run(['git', '-C', str(dest), 'sparse-checkout', 'init', '--cone'], check=True)
        subprocess.run(['git', '-C', str(dest), 'sparse-checkout', 'set',
                        'trunk/platform/sx430is', 'trunk/platform/sx420is',
                        'trunk/platform/sx410is', 'trunk/platform/sx400is',
                        'trunk/platform/ixus175_elph180', 'trunk/core', 'trunk/include',
                        'trunk/tools', 'trunk/platform/generic'], check=True)
    subprocess.run(['git', '-C', str(dest), 'checkout', '--detach', 'FETCH_HEAD'], check=True)
    actual = subprocess.check_output(['git', '-C', str(dest), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != item['commit']:
        raise RuntimeError('source revision mismatch')
print('Pinned checkouts fetched. No hardware functionality has been verified.')
