#!/usr/bin/env bash
set -euo pipefail
kit=$(cd -- "$(dirname -- "$0")/.." && pwd)
test "$#" -eq 1 || { echo 'Usage: bash tools/build-rom.sh /new/work/source'; exit 2; }
source_dir=$(realpath -- "$1")
python3 "$kit/tools/restore-source.py" "$source_dir" --verify
workspace=$(dirname -- "$source_dir")
mkdir -p "$workspace/tmp" "$workspace/ccache"
export OUT_DIR=out TMPDIR="$workspace/tmp" SOONG_NINJA=ninja
export TARGET_PRODUCT=lineage_beyond2qlte LINEAGE_BUILD=beyond2qlte
export TARGET_RELEASE=trunk_staging TARGET_BUILD_VARIANT=userdebug WITH_GMS=false
export BUILD_DATETIME=1793950146 BUILD_NUMBER=eng.user.los24.20261106
export BUILD_USERNAME=user BUILD_HOSTNAME=test-server
export KBUILD_BUILD_USER=nobody KBUILD_BUILD_HOST=android-build KBUILD_BUILD_VERSION=1
export KBUILD_BUILD_TIMESTAMP='Fri Nov 6 07:29:06 UTC 2026'
export NINJA_HIGHMEM_NUM_JOBS=2
if command -v ccache >/dev/null; then
    export USE_CCACHE=1 CCACHE_EXEC
    CCACHE_EXEC=$(command -v ccache)
    export CCACHE_DIR="$workspace/ccache"
fi
cd -- "$source_dir"
export PATH="$source_dir/prebuilts/jdk/jdk25/linux-x86/bin:$source_dir/out/host/linux-x86/bin:$PATH"
build/soong/soong_ui.bash --make-mode -j"${BUILD_JOBS:-12}" target-files-package validate_target_files check_target_files_vintf check_ota_package_signature
target="$source_dir/out/target/product/beyond2qlte/obj/PACKAGING/target_files_intermediates/lineage_beyond2qlte-target_files.zip"
release="$workspace/runtimefix8-rebuilt-release"
test ! -e "$release" || { echo 'Review the existing rebuilt release first; it will not be overwritten.'; exit 1; }
mkdir "$release"
python3 "$kit/tools/verify-target-files.py" "$target" "$release/payload-comparison.json"
key="$source_dir/external/avb/test/data/testkey_rsa4096.pem"
validate_target_files --verity_key "$key" --avb_recovery_key_path "$key" "$target" > "$release/native-files.log" 2>&1
check_target_files_vintf -v "$target" > "$release/vintf.log" 2>&1
rom="$release/lineage-24.0-20261110-UNOFFICIAL-beyond2qlte-runtimefix8-rebuilt.zip"
ota_from_target_files -k build/make/target/product/security/testkey "$target" "$rom" > "$release/ota-build.log" 2>&1
check_ota_package_signature build/make/target/product/security/testkey.x509.pem "$rom" > "$release/signature.log" 2>&1
sha256sum "$rom" > "$release/ROM.sha256"
echo "BUILD_AND_PAYLOAD_COMPARISON_PASSED: $release"
