#!/usr/bin/env bash
# Sourced by both baseline creation and strict rebuilds.
test -d "$source_dir" || return 2
workspace=$(dirname -- "$source_dir")
umask 022
mkdir -p "$workspace/tmp" "$workspace/ccache"
export OUT_DIR=out TMPDIR="$workspace/tmp" SOONG_NINJA=ninja
export TARGET_PRODUCT=lineage_beyond2qlte LINEAGE_BUILD=beyond2qlte
export TARGET_RELEASE=trunk_staging TARGET_BUILD_VARIANT=userdebug WITH_GMS=false
export BUILD_DATETIME=1793950146 BUILD_NUMBER=eng.user.los24.20261106
export BUILD_USERNAME=user BUILD_HOSTNAME=test-server
export KBUILD_BUILD_USER=nobody KBUILD_BUILD_HOST=android-build KBUILD_BUILD_VERSION=1
export KBUILD_BUILD_TIMESTAMP='Fri Nov 6 07:29:06 UTC 2026'
export SOURCE_DATE_EPOCH="$BUILD_DATETIME" TZ=UTC LC_ALL=C.UTF-8
export SMG9750_MODULE_SIGNING_KEY="$kit/inputs/kernel/module-signing-key.pem"
export NINJA_HIGHMEM_NUM_JOBS=2 SMG9750_REPRODUCIBLE_BUILD=1
unset ANDROID_BUILD_TOP OUT_DIR_COMMON_BASE CC_WRAPPER PYTHONOPTIMIZE E2FSPROGS_FAKE_TIME
if command -v ccache >/dev/null; then
    export USE_CCACHE=1 CCACHE_EXEC
    CCACHE_EXEC=$(command -v ccache)
    export CCACHE_DIR="$workspace/ccache"
fi
export PATH="$source_dir/prebuilts/jdk/jdk25/linux-x86/bin:$source_dir/out/host/linux-x86/bin:$PATH"
