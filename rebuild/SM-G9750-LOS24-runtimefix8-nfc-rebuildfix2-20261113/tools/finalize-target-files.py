#!/usr/bin/env python3
"""Put generated Recovery resources into the fixed vendor seed before release."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
import zipfile


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def quote(value):
    value = str(value)
    assert not any(c in value for c in '\n\r\0"\\')
    return '"' + value + '"'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    args.input, args.output, args.report = (p.resolve() for p in (args.input, args.output, args.report))
    kit = Path(__file__).resolve().parents[1]
    manifest = json.loads((kit / 'metadata/restore-manifest.json').read_text())
    seed = manifest['prebuilt_vendor_links']['vendor/samsung/sm8150-common/prebuilt/vendor.img']['sha256']
    assert not args.output.exists() and args.input.resolve() != args.output.resolve()
    host = source / 'out/host/linux-x86/bin'
    epoch = str(int(os.environ['BUILD_DATETIME']))
    env = dict(os.environ, PATH=str(host) + ':' + os.environ['PATH'], LC_ALL='C', TZ='UTC',
               E2FSPROGS_FAKE_TIME=epoch)
    avb = source / 'external/avb/avbtool.py'
    key = source / 'external/avb/test/data/testkey_rsa4096.pem'
    tools = {name: host / name for name in ('simg2img', 'img2simg', 'debugfs', 'e2fsck', 'e2fsdroid', 'add_img_to_target_files')}
    assert all(p.is_file() for p in tools.values())

    def run(command, **kwargs):
        return subprocess.run([str(a) for a in command], cwd=source, env=env, check=True, **kwargs)

    with tempfile.TemporaryDirectory(prefix='vendor-refresh-', dir=args.output.parent) as temporary:
        work = Path(temporary)
        # AVB follows the partition name when resolving its own descriptor.
        raw = work / 'vendor.img'
        sparse = work / 'vendor-sparse.img'
        blockmap = work / 'vendor.map'
        changed = ['/etc/recovery.img', '/bin/install-recovery.sh']
        with zipfile.ZipFile(args.input) as archive:
            names = archive.namelist()
            assert len(names) == len(set(names))
            assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
            for member, dest in [('IMAGES/vendor.img', sparse), ('IMAGES/vendor.map', blockmap)]:
                with archive.open(member) as src, dest.open('wb') as dst:
                    shutil.copyfileobj(src, dst)
            assert sha(sparse) == seed, 'Unexpected vendor seed'
            config = archive.read('META/vendor_filesystem_config.txt').decode()
            paths = sorted({'/' + row.split()[0].removeprefix('vendor').lstrip('/')
                            for row in config.splitlines() if row.split() and row.split()[0].startswith('vendor')})
            assert '/' in paths and len(paths) > 2600
            contents = {}
            for path in changed:
                member = 'VENDOR' + path
                assert stat.S_IFMT(archive.getinfo(member).external_attr >> 16) in (0, stat.S_IFREG)
                content = work / Path(path).name
                content.write_bytes(archive.read(member))
                contents[path] = content
            assert hashlib.sha256(archive.read('IMAGES/recovery.img')).hexdigest() == sha(contents['/etc/recovery.img'])

        run([tools['simg2img'], sparse, raw])
        partition_size = raw.stat().st_size
        info = run(['python3', avb, 'info_image', '--image', raw], capture_output=True, text=True).stdout
        assert 'Algorithm:                SHA256_RSA4096' in info
        assert re.search(r'Partition Name:\s+vendor\s*\n', info)
        assert set(re.findall(r'^\s*Flags:\s+(\d+)', info, re.M)) == {'0'}
        assert 'Prop:' not in info, 'Preserve unknown AVB properties explicitly'
        salt = re.search(r'Salt:\s+([0-9a-f]{64})\s*\n', info)[1]
        run(['python3', avb, 'verify_image', '--image', raw, '--key', key], stdout=subprocess.DEVNULL)
        stats = work / 'stat.commands'
        stats.write_text(''.join('stat ' + quote(p) + '\n' for p in paths))

        def metadata():
            result = run([tools['debugfs'], '-f', stats, raw], capture_output=True, text=True)
            blocks = re.split(r'^debugfs:\s+stat ', result.stdout, flags=re.M)[1:]
            assert len(blocks) == len(paths)
            rows = {}
            for block in blocks:
                path = shlex.split(block.splitlines()[0])[0]
                mode = re.search(r'Mode:\s+([0-7]+)', block)
                ids = re.search(r'User:\s+(\d+)\s+Group:\s+(\d+)', block)
                assert mode and ids
                attrs = sorted(line.strip() for line in block.splitlines() if re.match(r'\s+security\.', line))
                rows[path] = dict(mode=mode[1], uid=int(ids[1]), gid=int(ids[2]), attrs=attrs)
            return rows

        before = metadata()
        labels = {}
        for index, path in enumerate(changed):
            assert before[path]['uid'] == before[path]['gid'] == 0
            assert all(a.startswith('security.selinux ') for a in before[path]['attrs'])
            label = work / ('label-' + str(index))
            run([tools['debugfs'], '-R', 'ea_get -f ' + quote(label) + ' ' + quote(path) + ' security.selinux', raw],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            assert label.read_bytes().endswith(b'\0')
            labels[path] = label
        run(['python3', avb, 'erase_footer', '--image', raw])
        commands = []
        for path in changed:
            mode = '0' + format(stat.S_IFREG | int(before[path]['mode'], 8), 'o')
            commands += ['rm ' + quote(path), 'write ' + quote(contents[path]) + ' ' + quote(path),
                         'sif ' + quote(path) + ' mode ' + mode,
                         'sif ' + quote(path) + ' uid 0', 'sif ' + quote(path) + ' gid 0',
                         'ea_set -f ' + quote(labels[path]) + ' ' + quote(path) + ' security.selinux']
        command_file = work / 'write.commands'
        command_file.write_text('\n'.join(commands) + '\n')
        run([tools['debugfs'], '-w', '-f', command_file, raw], stdout=subprocess.DEVNULL)
        assert metadata() == before, 'Vendor modes, ownership or security attributes changed'
        for index, path in enumerate(changed):
            readback = work / ('readback-' + str(index))
            run([tools['debugfs'], '-R', 'dump ' + quote(path) + ' ' + quote(readback), raw],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            assert sha(readback) == sha(contents[path]), path
        # Fsck is read-only; use real time to avoid false future-time checks on the seed.
        fsck_env = {k: v for k, v in env.items() if k != 'E2FSPROGS_FAKE_TIME'}
        subprocess.run([str(tools['e2fsck']), '-fn', str(raw)], env=fsck_env, check=True,
                       stdout=subprocess.DEVNULL)
        run(['python3', avb, 'add_hashtree_footer', '--image', raw, '--partition_name', 'vendor',
             '--partition_size', str(partition_size), '--hash_algorithm', 'sha256', '--algorithm',
             'SHA256_RSA4096', '--key', key, '--salt', salt])
        run(['python3', avb, 'verify_image', '--image', raw, '--key', key], stdout=subprocess.DEVNULL)
        raw_sha = sha(raw)
        mapping_copy = work / 'mapping.img'
        shutil.copyfile(raw, mapping_copy)
        run([tools['e2fsdroid'], '-e', '-a', '/vendor', '-B', blockmap, mapping_copy])
        assert sha(mapping_copy) == raw_sha, 'Block map export changed the image'
        run([tools['img2simg'], raw, sparse])
        rebuilt_vendor_sha = sha(sparse)
        replacements = {'IMAGES/vendor.img': sparse, 'IMAGES/vendor.map': blockmap}
        omitted = {'IMAGES/vbmeta.img', 'META/vbmeta_digest.txt'}
        staged = work / 'target-files.zip'
        baseline = {}
        with zipfile.ZipFile(args.input) as archive, zipfile.ZipFile(staged, 'w', allowZip64=True) as output:
            for entry in archive.infolist():
                if entry.is_dir():
                    output.writestr(copy.copy(entry), b'')
                    continue
                h = hashlib.sha256()
                if entry.filename in omitted:
                    continue
                with archive.open(entry) as src:
                    if entry.filename in replacements:
                        for chunk in iter(lambda: src.read(8 * 1024 * 1024), b''):
                            h.update(chunk)
                        with replacements[entry.filename].open('rb') as updated, output.open(copy.copy(entry), 'w', force_zip64=True) as dst:
                            shutil.copyfileobj(updated, dst, 8 * 1024 * 1024)
                    else:
                        with output.open(copy.copy(entry), 'w', force_zip64=True) as dst:
                            for chunk in iter(lambda: src.read(8 * 1024 * 1024), b''):
                                h.update(chunk)
                                dst.write(chunk)
                baseline[entry.filename] = h.hexdigest()
        run([tools['add_img_to_target_files'], '--add_missing', staged])
        allowed = set(replacements) | omitted
        with zipfile.ZipFile(staged) as output:
            names = [i.filename for i in output.infolist() if not i.is_dir()]
            assert len(names) == len(set(names))
            assert set(names) == set(baseline) | omitted
            differences = []
            for name in names:
                h = hashlib.sha256()
                with output.open(name) as src:
                    for chunk in iter(lambda: src.read(8 * 1024 * 1024), b''):
                        h.update(chunk)
                if name not in baseline or baseline[name] != h.hexdigest():
                    assert name in allowed, 'Unexpected finalization change: ' + name
                    differences.append(name)
        report = dict(complete=True, input_sha256=sha(args.input), vendor_seed_sha256=seed,
                      vendor_raw_sha256=raw_sha, vendor_sparse_sha256=rebuilt_vendor_sha,
                      vendor_map_sha256=sha(blockmap), filesystem_metadata_paths=len(before),
                      metadata_unchanged=True, changed_vendor_paths=changed,
                      file_readback=True, AVB_verified=True, fsck=True, fixed_epoch=int(epoch),
                      changed_zip_entries=sorted(differences), phone_operations=False)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
        os.rename(staged, args.output)
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
