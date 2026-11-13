#!/usr/bin/env python3
"""Canonicalize unstable compiler metadata while retaining runtime contents."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import tempfile


class Elf:
    def __init__(self, path):
        self.data = Path(path).read_bytes()
        assert self.data[:6] == b'\x7fELF\x02\x01', 'Expected ELF64 little-endian'
        h = struct.unpack_from('<16sHHIQQQIHHHHHH', self.data)
        assert h[11] == 64 and h[12] and h[13] < h[12]
        self.machine = h[2]
        self.identity = (h[1], h[4], h[7])
        self.programs = self.data[h[5]:h[5] + h[9] * h[10]]
        headers = [struct.unpack_from('<IIQQQQIIQQ', self.data, h[6] + i * 64) for i in range(h[12])]
        sn = headers[h[13]]
        names = self.data[sn[4]:sn[4] + sn[5]]
        self.sections = []
        for s in headers:
            name = names[s[0]:].split(b'\0', 1)[0].decode()
            content = b'' if s[1] == 8 else self.data[s[4]:s[4] + s[5]]
            assert s[1] == 8 or len(content) == s[5]
            self.sections.append(dict(name=name, kind=s[1], flags=s[2], address=s[3], size=s[5],
                                      link=s[6], align=s[8], entry_size=s[9], data=content))
        self.by_name = {s['name']: s for s in self.sections}
        assert len(self.by_name) == len(self.sections)

    def runtime(self):
        return {s['name']: (s['kind'], s['flags'], s['address'], s['size'], s['align'], s['data'])
                for s in self.sections if s['flags'] & 2 and s['name'] != '.note.gnu.build-id'}


def string_at(strings, offset):
    assert 0 <= offset < len(strings)
    end = strings.find(b'\0', offset)
    assert end >= offset
    return strings[offset:end]


def lto(elf):
    assert elf.machine == 183, 'LTO normalization is limited to arm64'
    symbols = elf.by_name['.symtab']
    assert symbols['entry_size'] == 24 and len(symbols['data']) % 24 == 0
    strings = elf.sections[symbols['link']]['data']
    renames = {}
    for i in range(0, len(symbols['data']), 24):
        noff, info, other, section, value, size = struct.unpack_from('<IBBHQQ', symbols['data'], i)
        name = string_at(strings, noff).decode()
        match = re.fullmatch(r'(.*)\.llvm\.[0-9]+', name)
        if not match:
            continue
        assert info >> 4 == 0, 'Do not rename exported symbols'
        assert not re.search(r'\s', name)
        seed = (match[1] + '\0' + str(value) + '\0' + str(size)).encode()
        stable = match[1] + '.llvm.repro_' + hashlib.sha256(seed).hexdigest()[:16]
        assert name not in renames or renames[name] == stable
        renames[name] = stable
    if not renames:
        return {}, {}
    note = bytearray(elf.by_name['.note.gnu.build-id']['data'])
    namesz, descsz, kind = struct.unpack_from('<III', note)
    assert namesz == 4 and kind == 3 and note[12:16] == b'GNU\0' and descsz in (16, 20, 32)
    assert len(note) == 16 + descsz
    digest = hashlib.sha256()
    digest.update(struct.pack('<HQI', *elf.identity))
    digest.update(elf.programs)
    for name, row in sorted(elf.runtime().items()):
        digest.update(name.encode() + b'\0')
        digest.update(struct.pack('<IQQQQ', *row[:5]))
        digest.update(row[5])
    note[16:16 + descsz] = digest.digest()[:descsz]
    return {'.note.gnu.build-id': bytes(note)}, renames


def btf(elf):
    assert elf.machine == 247, 'Expected BPF object'
    data = elf.by_name['.BTF']['data']
    magic, version, flags, hdrlen, toff, tlen, soff, slen = struct.unpack_from('<HBBIIIII', data)
    assert magic == 0xeb9f and version == 1 and hdrlen == 24
    assert hdrlen + soff + slen == len(data) and toff + tlen <= soff
    strings = data[hdrlen + soff:]
    assert strings[:1] == strings[-1:] == b'\0'
    words = set(strings.split(b'\0'))
    records, pos = [], hdrlen + toff
    extra_size = {1: lambda n: 4, 2: lambda n: 0, 3: lambda n: 12, 4: lambda n: n * 12,
                  5: lambda n: n * 12, 6: lambda n: n * 8, 7: lambda n: 0, 8: lambda n: 0,
                  9: lambda n: 0, 10: lambda n: 0, 11: lambda n: 0, 12: lambda n: 0,
                  13: lambda n: n * 8, 14: lambda n: 4, 15: lambda n: n * 12,
                  16: lambda n: 0, 17: lambda n: 4, 18: lambda n: 0, 19: lambda n: n * 12}
    while pos < hdrlen + toff + tlen:
        noff, info, size = struct.unpack_from('<III', data, pos)
        kind, count = (info >> 24) & 31, info & 65535
        assert kind in extra_size
        length = 12 + extra_size[kind](count)
        row = bytearray(data[pos:pos + length])
        assert len(row) == length
        names = [0]
        refs = [8] if kind in (2, 8, 9, 10, 11, 12, 13, 14, 17, 18) else []
        if kind == 3:
            refs += [12, 16]
        elif kind in (4, 5):
            names += list(range(12, length, 12))
            refs += list(range(16, length, 12))
        elif kind == 6:
            names += list(range(12, length, 8))
        elif kind == 13:
            names += list(range(12, length, 8))
            refs += list(range(16, length, 8))
        elif kind == 15:
            refs += list(range(12, length, 12))
        elif kind == 19:
            names += list(range(12, length, 12))
        for p in names:
            words.add(string_at(strings, struct.unpack_from('<I', row, p)[0]))
        records.append(dict(data=row, kind=kind, names=names, refs=refs,
                            key=(string_at(strings, noff), info, size)))
        pos += length
    assert pos == hdrlen + toff + tlen
    forward = [i for i, r in enumerate(records) if r['kind'] == 7]
    assert len({records[i]['key'] for i in forward}) == len(forward), 'Ambiguous forward types'
    sorted_forward = sorted(forward, key=lambda i: records[i]['key'])
    ids = {old + 1: new + 1 for old, new in zip(sorted_forward, forward)}

    ext = bytearray(elf.by_name['.BTF.ext']['data'])
    emagic, ever, eflags, elen = struct.unpack_from('<HBBI', ext)
    assert emagic == magic and ever == version and elen in (24, 32)
    ext_names, ext_refs = [], []
    for slot, expected_size in [(8, 8), (16, 16), (24, 16)]:
        if slot >= elen:
            break
        off, length = struct.unpack_from('<II', ext, slot)
        if not length:
            continue
        at, end = elen + off, elen + off + length
        stride = struct.unpack_from('<I', ext, at)[0]
        assert stride >= expected_size and end <= len(ext)
        at += 4
        while at < end:
            secname, count = struct.unpack_from('<II', ext, at)
            ext_names.append(at)
            at += 8
            for _ in range(count):
                assert at + stride <= end
                if slot == 8:
                    ext_refs.append(at + 4)
                elif slot == 16:
                    ext_names += [at + 4, at + 8]
                else:
                    ext_refs.append(at + 4)
                    ext_names.append(at + 8)
                at += stride
        assert at == end
    for at in ext_names:
        words.add(string_at(strings, struct.unpack_from('<I', ext, at)[0]))
    canonical = bytearray(b'\0')
    offsets = {b'': 0}
    for word in sorted(words - {b''}):
        offsets[word] = len(canonical)
        canonical.extend(word + b'\0')

    def remap_names(buf, positions):
        for p in positions:
            old = struct.unpack_from('<I', buf, p)[0]
            struct.pack_into('<I', buf, p, offsets[string_at(strings, old)])

    def remap_types(buf, positions):
        for p in positions:
            old = struct.unpack_from('<I', buf, p)[0]
            assert old <= len(records)
            struct.pack_into('<I', buf, p, ids.get(old, old))

    for row in records:
        remap_names(row['data'], row['names'])
        remap_types(row['data'], row['refs'])
    remap_names(ext, ext_names)
    remap_types(ext, ext_refs)
    ordered = list(records)
    for new, old in zip(forward, sorted_forward):
        ordered[new] = records[old]
    start, end = hdrlen + toff, hdrlen + toff + tlen
    result = bytearray(data[:start])
    result.extend(b''.join(r['data'] for r in ordered))
    result.extend(data[end:hdrlen + soff])
    result.extend(canonical)
    struct.pack_into('<I', result, 20, len(canonical))
    return {'.BTF': bytes(result), '.BTF.ext': bytes(ext)}, {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['lto', 'btf'])
    parser.add_argument('objcopy', type=Path)
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    before = Elf(args.file)
    replacements, renames = (lto if args.mode == 'lto' else btf)(before)
    replacements = {name: value for name, value in replacements.items() if value != before.by_name[name]['data']}
    if not replacements and not renames:
        return
    mode = stat.S_IMODE(args.file.stat().st_mode)
    with tempfile.TemporaryDirectory(prefix='.repro-', dir=args.file.parent) as temporary:
        temporary = Path(temporary)
        command = [str(args.objcopy)]
        if renames:
            mapping = temporary / 'symbols'
            mapping.write_text(''.join(a + ' ' + b + '\n' for a, b in sorted(renames.items())))
            command += ['--redefine-syms', str(mapping)]
        for i, (name, value) in enumerate(replacements.items()):
            content = temporary / str(i)
            content.write_bytes(value)
            command += ['--update-section', name + '=' + str(content)]
        output = temporary / 'output'
        subprocess.run([*command, str(args.file), str(output)], check=True)
        after = Elf(output)
        assert before.runtime() == after.runtime(), 'Runtime sections changed'
        assert before.programs == after.programs, 'Program layout changed'
        if args.mode == 'btf':
            assert {n: s['data'] for n, s in before.by_name.items() if n not in ('.BTF', '.BTF.ext')} == {
                n: s['data'] for n, s in after.by_name.items() if n not in ('.BTF', '.BTF.ext')}
        output.chmod(mode)
        os.replace(output, args.file)


if __name__ == '__main__':
    main()
