#!/usr/bin/env bash
set -euo pipefail
kit=$(cd -- "$(dirname -- "$0")/.." && pwd)
test "$#" -eq 1 || { echo 'Usage: bash tools/build-rom.sh /new/work/source'; exit 2; }
source_dir=$(realpath -- "$1")
test -f "$kit/metadata/reproduction-contract.json" || { echo 'The candidate baseline has not been accepted.'; exit 2; }
source "$kit/tools/build-environment.sh"
python3 "$kit/tools/restore-source.py" "$source_dir" --verify
cd -- "$source_dir"
build/soong/soong_ui.bash --make-mode --skip-ninja -j"${BUILD_JOBS:-12}" target-files-package validate_target_files check_target_files_vintf check_ota_package_signature out/host/linux-x86/bin/debugfs out/host/linux-x86/bin/e2fsck out/host/linux-x86/bin/e2fsdroid out/host/linux-x86/bin/simg2img out/host/linux-x86/bin/img2simg add_img_to_target_files ota_from_target_files aprotoc out/host/linux-x86/bin/brotli
python3 "$kit/tools/check-kernel-flags.py" "$source_dir"
build/soong/soong_ui.bash --make-mode -j"${BUILD_JOBS:-12}" target-files-package validate_target_files check_target_files_vintf check_ota_package_signature out/host/linux-x86/bin/debugfs out/host/linux-x86/bin/e2fsck out/host/linux-x86/bin/e2fsdroid out/host/linux-x86/bin/simg2img out/host/linux-x86/bin/img2simg add_img_to_target_files ota_from_target_files aprotoc out/host/linux-x86/bin/brotli
target="$source_dir/out/target/product/beyond2qlte/obj/PACKAGING/target_files_intermediates/lineage_beyond2qlte-target_files.zip"
release="$workspace/runtimefix8-nfc-rebuildfix2-release"
test ! -e "$release" || { echo 'Review the existing release first; it will not be overwritten.'; exit 1; }
mkdir "$release"
python3 "$kit/tools/finalize-target-files.py" "$source_dir" "$target" "$release/target-files.zip" "$release/vendor-finalization.json" > "$release/vendor-finalization.log" 2>&1
target="$release/target-files.zip"
python3 "$kit/tools/verify-target-files.py" "$target" "$release/payload-comparison.json"
key="$source_dir/external/avb/test/data/testkey_rsa4096.pem"
validate_target_files --verity_key "$key" --avb_recovery_key_path "$key" "$target" > "$release/native-files.log" 2>&1
check_target_files_vintf -v "$target" > "$release/vintf.log" 2>&1
rom="$release/lineage-24.0-20261113-UNOFFICIAL-beyond2qlte-runtimefix8-nfc-rebuildfix2.zip"
ota_from_target_files -k build/make/target/product/security/testkey "$target" "$rom" > "$release/ota-build.log" 2>&1
check_ota_package_signature build/make/target/product/security/testkey.x509.pem "$rom" > "$release/signature.log" 2>&1
python3 "$kit/tools/verify-ota.py" "$source_dir" "$target" "$rom" "$release/ota-verification.json" > "$release/ota-verification.log" 2>&1
sha256sum "$rom" "$target" > "$release/SHA256SUMS"
echo "BUILD_PAYLOAD_AND_NATIVE_VERIFICATION_PASSED: $release"
