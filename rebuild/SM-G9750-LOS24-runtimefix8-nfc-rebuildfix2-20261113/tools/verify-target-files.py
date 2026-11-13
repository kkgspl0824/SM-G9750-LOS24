#!/usr/bin/env python3
"""Reject a rebuild with payload differences; do not silently waive missing fixes."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('target_files', type=Path)
parser.add_argument('report', type=Path)
args = parser.parse_args()
kit = Path(__file__).resolve().parents[1]
expected = json.loads((kit / 'metadata/reproduction-contract.json').read_text())
with zipfile.ZipFile(args.target_files) as tf:
    names = [m.filename for m in tf.infolist()]
    assert len(names) == len(set(names))
    actual = {}
    for m in tf.infolist():
        if not m.is_dir() and m.filename.startswith(('SYSTEM/', 'VENDOR/', 'ROOT/', 'BOOT/', 'RECOVERY/', 'IMAGES/')):
            h = hashlib.sha256()
            with tf.open(m) as stream:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                    h.update(block)
            actual[m.filename] = h.hexdigest()
baseline = dict(expected['runtime_files'], **expected['image_files'])
missing = sorted(set(baseline) - set(actual))
added = sorted(set(actual) - set(baseline))
changed = {name: dict(expected=baseline[name], actual=actual[name]) for name in baseline.keys() & actual.keys() if baseline[name] != actual[name]}
report = dict(complete=True, matches_reference=not (missing or added or changed),
    baseline_ROM_sha256=expected['latest_ROM_sha256'], compared_files=len(baseline),
    missing=missing, added=added, changed=changed,
    note='Payload equality is checked; whole-ZIP byte identity is not promised. A mismatch requires review before release.')
args.report.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(matches_reference=report['matches_reference'], missing=len(missing), added=len(added), changed=len(changed)), indent=2))
raise SystemExit(0 if report['matches_reference'] else 2)
