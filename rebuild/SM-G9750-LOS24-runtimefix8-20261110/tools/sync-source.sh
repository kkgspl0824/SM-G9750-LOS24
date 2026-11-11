#!/usr/bin/env bash
set -euo pipefail
kit=$(cd -- "$(dirname -- "$0")/.." && pwd)
test "$#" -eq 1 || { echo 'Usage: bash tools/sync-source.sh /new/work/source'; exit 2; }
command -v git >/dev/null
git lfs version >/dev/null
source_dir=$(realpath -m -- "$1")
mkdir -p -- "$source_dir"
marker="$source_dir/.runtimefix8-sync-manifest"
expected=$(sha256sum "$kit/manifests/pinned.xml" | cut -d' ' -f1)
if test ! -e "$marker"; then
    test -z "$(ls -A -- "$source_dir")" || { echo 'Use an empty source directory; existing files will not be removed.'; exit 1; }
    printf '%s\n' "$expected" > "$marker"
else
    test "$(cat "$marker")" = "$expected"
fi
test ! -e "$source_dir/.runtimefix8-restored.json" || { echo 'Sources already restored; use restore-source.py --verify instead of syncing.'; exit 1; }
cd -- "$source_dir"
"$kit/tools/repo" init -u https://github.com/LineageOS/android.git -b lineage-24.0 --repo-rev=v2.71 --depth=1 --git-lfs
# A standalone exported manifest contains every project at a fixed SHA.
if test -L .repo/manifest.xml; then rm .repo/manifest.xml; fi
cp -- "$kit/manifests/pinned.xml" .repo/manifest.xml
"$kit/tools/repo" sync -c -j"${SYNC_JOBS:-4}" --no-clone-bundle
python3 "$kit/tools/restore-source.py" "$source_dir"
