#!/usr/bin/env python3
"""Reject a generated kernel command that lost the device's debug path root."""
from pathlib import Path
import re
import os
import sys


def roots(text):
    return set(re.findall(r'SMG9750_SOURCE_ROOT=([^\s]+)', text))


assert roots('make -j12') == set()
assert roots('make SMG9750_SOURCE_ROOT=/test/source -C kernel') == {'/test/source'}
source = Path(sys.argv[1]).resolve()
text = (source / 'out/build-lineage_beyond2qlte.ninja').read_text()
commands = [line for line in text.splitlines() if line.lstrip().startswith('command =')
            and 'KERNEL_OBJ' in line and (' -C kernel/samsung/sm8150-common ' in line
                or ' -C ' + str(source / 'kernel/samsung/sm8150-common') + ' ' in line)]
assert commands, 'Generated kernel Make commands not found'
assert all(roots(line) == {str(source)} for line in commands), 'Kernel source root was lost before the generated Make commands'
kit = Path(__file__).resolve().parents[1]
key_path = kit / 'inputs/kernel/module-signing-key.pem'
assert key_path.is_file()
for command in commands:
    assert set(re.findall(r'SOURCE_DATE_EPOCH=([^\s]+)', command)) == {os.environ['BUILD_DATETIME']}, 'Kernel clock input missing'
    assert set(re.findall(r'SMG9750_MODULE_SIGNING_KEY=([^\s]+)', command)) == {str(key_path)}, 'Kernel signing input missing'
print('GENERATED_KERNEL_ROOT_CLOCK_AND_SIGNING_INPUTS_VERIFIED')
