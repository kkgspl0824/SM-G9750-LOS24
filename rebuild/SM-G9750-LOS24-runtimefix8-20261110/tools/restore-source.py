#!/usr/bin/env python3
"""Restore only onto pristine pinned checkouts; never discard existing changes."""
from pathlib import Path
import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess

kit = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('--verify', action='store_true')
args = parser.parse_args()
source = args.source.resolve()
data = json.loads((kit / 'metadata/restore-manifest.json').read_text())
env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe_path(base, relative):
    p = Path(relative)
    assert not p.is_absolute() and '..' not in p.parts and p.parts
    result = base / p
    assert not any(parent.is_symlink() for parent in result.parents if parent != base and base in parent.parents)
    return result


assert source.is_dir() and source != kit and not kit.is_relative_to(source)
assert sha(kit / 'source-changes/modified-source-files.tar.gz') == data['source_archive_sha256']
assert sha(kit / 'manifests/pinned.xml') == data['manifest_sha256']
for project, info in data['changed_projects'].items():
    assert sha(safe_path(kit / 'source-changes', info['patch'])) == info['sha256']
for relative, info in data['prebuilt_vendor_links'].items():
    assert sha(safe_path(kit, info['file'])) == info['sha256']


def head(project):
    p = safe_path(source, project)
    actual = subprocess.check_output(['git', '-C', str(p), 'rev-parse', 'HEAD'], env=env, text=True).strip()
    assert actual == data['project_heads'][project], 'Wrong source revision: ' + project
    if not args.verify and not (source / '.runtimefix8-restored.json').exists():
        status = subprocess.check_output(['git', '-C', str(p), 'status', '--porcelain', '--untracked-files=normal'], env=env)
        assert not status, 'Existing changes must be reviewed first: ' + project


with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    list(pool.map(head, data['project_heads']))
marker = source / '.runtimefix8-restored.json'
if not args.verify and not marker.exists():
    for project, info in data['changed_projects'].items():
        patch = kit / 'source-changes' / info['patch']
        subprocess.run(['git', '-C', str(source / project), 'apply', '--check', '--binary', str(patch)], env=env, check=True)
    for project, info in data['changed_projects'].items():
        patch = kit / 'source-changes' / info['patch']
        subprocess.run(['git', '-C', str(source / project), 'apply', '--binary', '--whitespace=nowarn', str(patch)], env=env, check=True)
    for relative, info in data['prebuilt_vendor_links'].items():
        p = safe_path(source, relative)
        assert not p.exists() and not p.is_symlink(), 'Unexpected prebuilt input: ' + relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.symlink_to(os.path.relpath(kit / info['file'], p.parent))
    # Git only records executable bits; restore the captured non-executable permissions too.
    for relative, info in data['entries'].items():
        if info['kind'] == 'file':
            p = safe_path(source, relative)
            assert p.is_file() and not p.is_symlink() and not info['mode'] & 0o7000
            p.chmod(info['mode'])

for relative, info in data['entries'].items():
    p = safe_path(source, relative)
    if info['kind'] == 'symlink':
        assert p.is_symlink() and os.readlink(p) == info['target'], relative
    else:
        assert p.is_file() and not p.is_symlink() and sha(p) == info['sha256'], relative
        assert (p.stat().st_mode & 0o7777) == info['mode'], 'Wrong source mode: ' + relative
for relative in data['deleted']:
    p = safe_path(source, relative)
    assert not p.exists() and not p.is_symlink(), 'Unexpected deleted source remains: ' + relative
for relative, digest in data['latest_84_source_hashes'].items():
    assert sha(safe_path(source, relative)) == digest, relative
for relative, info in data['prebuilt_vendor_links'].items():
    p = safe_path(source, relative)
    assert p.is_symlink() and p.resolve() == (kit / info['file']).resolve() and sha(p) == info['sha256'], relative
if not args.verify:
    marker.write_text(json.dumps(dict(complete=True, manifest_sha256=data['manifest_sha256'],
        projects=len(data['project_heads']), restored_files=len(data['entries']),
        kit_location=str(kit), no_original_server_path_required=True), indent=2) + '\n')
print('PINNED_HEADS_SOURCE_CHANGES_AND_VENDOR_INPUTS_VERIFIED')
