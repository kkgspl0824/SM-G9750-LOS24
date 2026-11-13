#
# Copyright (C) 2020 The LineageOS Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Vendor is repacked with generated policy; do not use stock-policy compatibility mode.
TARGET_USES_PREBUILT_VENDOR_SEPOLICY := false

# Inherit common board flags
include device/samsung/sm8150-common/BoardConfigCommon.mk

DEVICE_PATH := device/samsung/beyond2qlte

# SM-G9750 boots the system partition as root and enters /init without arguments.
$(call soong_config_set_bool,init,legacy_system_as_root,true)

# Stock vendor and recovery use these two names for SM-G9750.
TARGET_OTA_ASSERT_DEVICE := beyond2qlte,beyond2q

#WITH_GMS := true

# APEX
#DEXPREOPT_GENERATE_APEX_IMAGE := true

# Bluetooth
BOARD_BLUETOOTH_BDROID_BUILDCFG_INCLUDE_DIR := $(DEVICE_PATH)/bluetooth

# FOD
$(call soong_config_set,surfaceflinger,udfps_lib,//hardware/samsung:libudfps_extension.samsung)

# Fingerprint
DEVICE_MANIFEST_FILE := $(DEVICE_PATH)/configs/manifest.xml
DEVICE_MATRIX_FILE := $(DEVICE_PATH)/configs/compatibility_matrix.xml
DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += $(DEVICE_PATH)/configs/vendor_extensions_matrix.xml
TARGET_VENDOR_PROP += $(DEVICE_PATH)/vendor.prop

# HXE1 EFS rules apply only to this product.
SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/system_ext
BOARD_VENDOR_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/vendor

# This 4.14 vendor still allocates secure buffers through /dev/ion.
include device/lineage/sepolicy/libion/sepolicy.mk

# Kernel
TARGET_KERNEL_CONFIG := lineage_sm_g9750_defconfig
TARGET_KERNEL_CONFIG_EXT :=
TARGET_KERNEL_CLANG_PATH := $(abspath prebuilts/clang/host/linux-x86-kernel-4.14/clang-r383902b1)
TARGET_KERNEL_LLVM_BINUTILS := false
KERNEL_CC := CC=clang
# Samsung 4.14 needs the paired GNU binutils with Clang 11.
KERNEL_CROSS_COMPILE := CROSS_COMPILE=$(abspath prebuilts/gcc/linux-x86/aarch64/aarch64-linux-android-4.9)/bin/aarch64-linux-android- CROSS_COMPILE_ARM32=$(abspath prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9)/bin/arm-linux-androideabi-
TARGET_KERNEL_MIXED_MODE := false
TARGET_KERNEL_ADDITIONAL_FLAGS := HOSTCC=/usr/bin/gcc HOSTCFLAGS=-B/usr/bin HOSTLDFLAGS=-B/usr/bin -j12 KBUILD_BUILD_VERSION=1 KBUILD_BUILD_TIMESTAMP="$(shell LC_ALL=C date -u -d @$(shell cat $(BUILD_DATETIME_FILE)))" KBUILD_BUILD_USER=nobody KBUILD_BUILD_HOST=android-build
TARGET_KERNEL_ADDITIONAL_FLAGS += LLVM= LLVM_IAS=
TARGET_KERNEL_ADDITIONAL_FLAGS += SMG9750_SOURCE_ROOT=$(abspath .)
TARGET_KERNEL_ADDITIONAL_FLAGS += SOURCE_DATE_EPOCH=$(shell cat $(BUILD_DATETIME_FILE))
TARGET_KERNEL_ADDITIONAL_FLAGS += SMG9750_MODULE_SIGNING_KEY=$(SMG9750_MODULE_SIGNING_KEY)
TARGET_KERNEL_SOURCE := kernel/samsung/sm8150-common
BOARD_BOOT_HEADER_VERSION := 1
BOARD_KERNEL_BASE := 0x00000000
BOARD_KERNEL_CMDLINE := androidboot.boot_devices=soc/1d84000.ufshc console=null androidboot.hardware=qcom androidboot.memcg=1 lpm_levels.sleep_disabled=1 video=vfb:640x400,bpp=32,memsize=3072000 msm_rtb.filter=0x237 service_locator.enable=1 androidboot.usbcontroller=a600000.dwc3 swiotlb=2048 printk.devkmsg=on firmware_class.path=/vendor/firmware_mnt/image
BOARD_KERNEL_IMAGE_NAME := Image-dtb
# Native Image-dtb contains the Samsung uncompressed header and both base DTBs.
BOARD_INCLUDE_DTB_IN_BOOTIMG :=
BOARD_KERNEL_APPEND_DTBS :=
BOARD_DTBO_CFG := $(DEVICE_PATH)/kernel/dtbo.cfg
# Audio and all three HXE1 module replacements are built into the paired kernel.
BOARD_VENDOR_KERNEL_MODULES_LOAD :=
BOARD_KERNEL_OFFSET := 0x00008000
BOARD_KERNEL_PAGESIZE := 4096
BOARD_KERNEL_TAGS_OFFSET := 0x01E00000
BOARD_KERNEL_SECOND_OFFSET := 0x00F00000
BOARD_RAMDISK_OFFSET := 0x02000000
BOARD_DTB_OFFSET := 0x01F00000
BOARD_MKBOOTIMG_ARGS := --kernel_offset $(BOARD_KERNEL_OFFSET) --ramdisk_offset $(BOARD_RAMDISK_OFFSET) --dtb_offset $(BOARD_DTB_OFFSET) --tags_offset $(BOARD_KERNEL_TAGS_OFFSET) --second_offset $(BOARD_KERNEL_SECOND_OFFSET)
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)

# Partitions
BUILD_WITHOUT_VENDOR := false
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_VENDORIMAGE_PARTITION_SIZE := 1379926016
BOARD_PREBUILT_VENDORIMAGE := vendor/samsung/sm8150-common/prebuilt/vendor.img
BOARD_FLASH_BLOCK_SIZE := 262144
BOARD_BOOTIMAGE_PARTITION_SIZE := 67108864
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 82825216
BOARD_DTBOIMG_PARTITION_SIZE := 10485760
BOARD_CACHEIMAGE_PARTITION_SIZE := 629145600
BOARD_CACHEIMAGE_FILE_SYSTEM_TYPE := ext4
# USERDATA grows to the remaining space in the stock PIT; do not build a fixed-size userdata image.
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 6071255040
BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE := ext4
TARGET_COPY_OUT_PRODUCT := system/product

# Recovery
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/rootdir/etc/fstab.qcom

# Root
TARGET_FS_CONFIG_GEN := $(DEVICE_PATH)/config.fs

# Soong namespaces
PRODUCT_SOONG_NAMESPACES += $(DEVICE_PATH)

#TARGET_INIT_VENDOR_LIB := //$(DEVICE_PATH):libinit_beyond2qlte
#TARGET_RECOVERY_DEVICE_MODULES := libinit_beyond2qlte

# Explicitly approved experimental SM-G9750 profile; Samsung rejects custom AVB roots with flags0.
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --set_hashtree_disabled_flag
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --flags 2

# Keep Recovery resources identical across build goals with the same build inputs.
BOARD_AVB_RECOVERY_ADD_HASH_FOOTER_ARGS := $(BOARD_AVB_RECOVERY_ADD_HASH_FOOTER_ARGS) --salt $(shell sha256sum $(BUILD_NUMBER_FILE) $(BUILD_DATETIME_FILE) | sha256sum | cut -d " " -f 1)
