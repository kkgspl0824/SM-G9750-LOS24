#!/usr/bin/env python3
"""Validate a native full OTA and reconstruct its block payloads without flashing."""
from pathlib import Path
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
source = Path(sys.argv[1]).resolve()
target = Path(sys.argv[2]).resolve()
rom = Path(sys.argv[3]).resolve()
report_path = Path(sys.argv[4]).resolve()
artifact = report_path.parent
tools = source / 'out/host/linux-x86/bin'
def ranges(text, limit):
    numbers = [int(n) for n in text.split(',')]
    assert numbers[0] == len(numbers) - 1 and numbers[0] % 2 == 0
    result = list(zip(numbers[1::2], numbers[2::2]))
    assert all(0 <= start < end <= limit for start, end in result)
    assert all(a[1] <= b[0] for a, b in zip(result, result[1:]))
    return result
for text in ['1,0', '2,0,2', '4,0,1,0,1']:
    try:
        ranges(text, 1)
    except AssertionError:
        pass
    else:
        raise AssertionError('Invalid block range accepted: ' + text)
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()
report = {'phone_operations': False, 'runtime_ready': False}
with zipfile.ZipFile(rom) as ota, zipfile.ZipFile(target) as tf:
    names = ota.namelist()
    assert len(names) == len(set(names)) and ota.testzip() is None
    assert all(not n.startswith('/') and '..' not in Path(n).parts for n in names)
    assert 'payload.bin' not in names
    metadata = dict(line.split('=', 1) for line in ota.read('META-INF/com/android/metadata').decode().splitlines() if '=' in line)
    props = dict(line.split('=', 1) for line in tf.read('SYSTEM/build.prop').decode().splitlines() if '=' in line and not line.startswith('#'))
    assert props['ro.build.version.sdk'] == '37' and props['ro.build.version.release'] == '17'
    assert metadata['ota-type'] == 'BLOCK' and metadata['post-build'] == props['ro.build.fingerprint']
    assert set(re.split(r'[,|]', metadata['pre-device'])) == {'beyond2qlte', 'beyond2q'}
    assert metadata.get('ota-wipe') != 'yes'
    assert metadata.get('spl-downgrade') != 'yes'
    decoded = subprocess.run([str(source / 'out/host/linux-x86/bin/aprotoc'), '--decode=build.tools.releasetools.OtaMetadata',
        '--proto_path=' + str(source / 'build/make/tools/releasetools'), 'ota_metadata.proto'],
        input=ota.read('META-INF/com/android/metadata.pb'), capture_output=True, check=True)
    proto_text = decoded.stdout.decode()
    assert 'wipe: true' not in proto_text and 'spl_downgrade: true' not in proto_text
    assert 'downgrade: true' not in proto_text
    (artifact / 'metadata-decoded.txt').write_text(proto_text)
    report.update(metadata_proto_wipe=False, metadata_proto_SPL_downgrade=False,
                  clean_install=False, no_wipe=True, Recovery_write=True, vbmeta_write=False, actual_security_patch=props['ro.build.version.security_patch'])
    script = ota.read('META-INF/com/google/android/updater-script').decode()
    (artifact / 'updater-script.txt').write_text(script)
    assert set(re.findall(r'getprop\("ro\.(?:product\.device|build\.product)"\) == "([^"]+)"', script)) == {'beyond2qlte', 'beyond2q'}
    assert not re.search(r'\bformat\s*\(', script)
    assert 'run_program("/tmp/install/bin/backuptool.sh"' not in script
    assert script.count('assert(package_extract_file("recovery.img", "/dev/block/bootdevice/by-name/recovery"));') == 1
    assert not re.search(r'\bdelete(?:_recursive)?\s*\(\s*"/data(?:/|")', script)
    assert 'userdata' not in script

    assert 'samsung.verify_trustzone' not in script
    assert 'package_extract_file("vbmeta.img"' not in script
    writes = set(re.findall(r'/dev/block/bootdevice/by-name/([A-Za-z0-9_]+)', script))
    assert {'system', 'vendor', 'boot', 'dtbo', 'vbmeta'} <= writes
    assert writes <= {'system', 'vendor', 'boot', 'dtbo', 'vbmeta', 'recovery', 'cache', 'misc'}
    approved_sha1 = '1397b2d33cb3e75a80efc1dd7885b90425477359'
    guard = 'range_sha1("/dev/block/bootdevice/by-name/vbmeta", "2,0,1") == "' + approved_sha1 + '"'
    assert script.count(guard) == 2 and script.index(guard) < script.index('block_image_update(')
    native_guard = 'range_sha1("/dev/block/bootdevice/by-name/vbmeta", "2,0,1") == "' + hashlib.sha1(tf.read('IMAGES/vbmeta.img')).hexdigest() + '"'
    assert script.count(native_guard) == 2
    unlocked = '(getprop("ro.boot.vbmeta.device_state") == "unlocked" || getprop("ro.boot.verifiedbootstate") == "orange")'
    exact_guard = '(%s && (%s || %s))' % (unlocked, native_guard, guard)
    assert script.count(exact_guard) == 2 and 'assert(' + exact_guard + ');' in script
    report['readonly_vbmeta_guard'] = {'approved_baseline_sha256': '83438dff4b72eaeaf6f773e1695c4d1f4abaedd79a0ac47f38d9bb048fbd6313', 'approved_baseline_sha1': approved_sha1, 'native_image_sha1': hashlib.sha1(tf.read('IMAGES/vbmeta.img')).hexdigest(), 'exact_unlocked_guard_occurrences': 2, 'vbmeta_write': False}
    assert 'ro.boot.vbmeta.device_state' in script and 'unlocked' in script
    report['image_payloads'] = {}
    for name in ['boot.img', 'recovery.img', 'dtbo.img', 'vbmeta.img']:
        data = ota.read(name)
        assert data == tf.read('IMAGES/' + name), name
        report['image_payloads'][name] = hashlib.sha256(data).hexdigest()
    updater = ota.read('META-INF/com/google/android/update-binary')
    assert updater == tf.read('OTA/bin/updater')
    assert updater[:5] == b'\x7fELF\x02' and int.from_bytes(updater[18:20], 'little') == 183
    cert = (source / 'build/make/target/product/security/testkey.x509.pem').read_bytes()
    with zipfile.ZipFile(io.BytesIO(tf.read('RECOVERY/RAMDISK/system/etc/security/otacerts.zip'))) as trust:
        assert cert in [trust.read(n) for n in trust.namelist()]
    report['full_block_payloads'] = {}
    with tempfile.TemporaryDirectory(prefix='los24-ota-verify-', dir=Path(os.environ['TMPDIR'])) as directory:
        temp = Path(directory)
        for part, size in [('system', 6071255040), ('vendor', 1379926016)]:
            lines = ota.read(part + '.transfer.list').decode().splitlines()
            assert lines[0] == '4' and lines[2:4] == ['0', '0']
            sparse, raw, rebuilt = [temp / (part + suffix) for suffix in ['.sparse', '.raw', '.rebuilt']]
            with tf.open('IMAGES/' + part + '.img') as src, sparse.open('wb') as dst:
                shutil.copyfileobj(src, dst, 8 * 1024 * 1024)
            subprocess.run([str(tools / 'simg2img'), str(sparse), str(raw)], check=True)
            assert raw.stat().st_size == size
            name = part + '.new.dat'
            if name in names:
                stream = ota.open(name)
            else:
                compressed = temp / (name + '.br')
                with ota.open(name + '.br') as src, compressed.open('wb') as dst:
                    shutil.copyfileobj(src, dst, 8 * 1024 * 1024)
                decompressed = temp / name
                subprocess.run([str(tools / 'brotli'), '--decompress', '--output=' + str(decompressed), str(compressed)], check=True)
                stream = decompressed.open('rb')
            count = 0
            with stream, rebuilt.open('w+b') as dst:
                dst.truncate(size)
                for line in lines[4:]:
                    command, encoded = line.split()
                    assert command in {'new', 'zero', 'erase'}, command
                    for start, end in ranges(encoded, size // 4096):
                        if command != 'new': continue
                        dst.seek(start * 4096)
                        remaining = (end - start) * 4096
                        count += end - start
                        while remaining:
                            data = stream.read(min(8 * 1024 * 1024, remaining))
                            assert data, (part, 'truncated new.dat')
                            dst.write(data)
                            remaining -= len(data)
                assert stream.read(1) == b'', 'Unconsumed new.dat'
            assert sha(rebuilt) == sha(raw), part
            report['full_block_payloads'][part] = {'bytes': size, 'new_blocks': count, 'raw_sha256': sha(raw), 'reconstruction': 'passed'}
            print('FULL_BLOCK_PAYLOAD_VERIFIED', part, flush=True)
report.update(complete=True, ROM_sha256=sha(rom), ROM_bytes=rom.stat().st_size,
              metadata=metadata, referenced_partitions=sorted(writes), signature='verify separately with native check_ota_package_signature')
report_path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2), flush=True)
