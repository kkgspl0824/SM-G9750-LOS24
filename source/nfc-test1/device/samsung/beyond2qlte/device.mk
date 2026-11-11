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

DEVICE_PATH := device/samsung/beyond2qlte


# Inherit common device configuration
$(call inherit-product, device/samsung/sm8150-common/common.mk)
ifeq ($(WITH_GMS), true)
	$(call inherit-product, vendor/partner_gms/products/gms.mk)
endif

PRODUCT_SHIPPING_API_LEVEL := 28
# Validate the actual kernel/config even though this device shipped before API 29.
PRODUCT_OTA_ENFORCE_VINTF_KERNEL_REQUIREMENTS := true
# This kernel has neither USERFAULTFD nor MREMAP_DONTUNMAP.
PRODUCT_ENABLE_UFFD_GC := false
# The paired 4.14 kernel supports ext4, without an EROFS driver.
PRODUCT_DEFAULT_APEX_PAYLOAD_TYPE := ext4

# Overlays
DEVICE_PACKAGE_OVERLAYS += \
    $(DEVICE_PATH)/overlay \
    $(DEVICE_PATH)/overlay-lineage

PRODUCT_PACKAGE_OVERLAYS += $(DEVICE_PATH)/overlay-product

# VNDK
PRODUCT_EXTRA_VNDK_VERSIONS += 30

# Audio
# The verified G9750ZHU8HXE1 vendor uses VNDK 30.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/audio/audio_policy_configuration.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio_policy_configuration.xml

# Display
PRODUCT_PRODUCT_PROPERTIES += \
    ro.sf.lcd_density=560

# Preserve HXE1 power hints through the private legacy0 service; add DT2W.
PRODUCT_PACKAGES += android.hardware.power-service.beyond2qlte

# Fingerprint
PRODUCT_SOONG_NAMESPACES += hardware/samsung
PRODUCT_PACKAGES += \
    android.hardware.biometrics.fingerprint-service.samsung.beyond2qlte

PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.fingerprint.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.fingerprint.xml \
    $(DEVICE_PATH)/rootdir/etc/zz-init.beyond2qlte.fingerprint.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/zz-init.beyond2qlte.fingerprint.rc

# Init
PRODUCT_PACKAGES += \
	fstab.qcom \
    00-smg9750-legacy-metadata.rc

# The kernel mounts system as root; only vendor remains for first-stage init.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/rootdir/etc/fstab.qcom.first_stage:$(TARGET_COPY_OUT_SYSTEM)/etc/fstab.qcom

PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/rootdir/etc/ueventd.vendor-import.rc:$(TARGET_COPY_OUT_VENDOR)/etc/ueventd.rc

# Keep the existing Recovery during diagnostic and data-preserving updates.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/rootdir/etc/zz-init.beyond2qlte.recovery-guard.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/zz-init.beyond2qlte.recovery-guard.rc

# Skip Mount
PRODUCT_PACKAGES += \
    gsi_skip_mount.cfg
	
# HXE1 device and native 4.14 kernel both retain FCM 4 requirements.
PRODUCT_PACKAGES += framework_compatibility_matrix.4.xml

# Real 5.4 BPF ABI backports passed the device probe; uname remains 4.14.190.
PRODUCT_SYSTEM_PROPERTIES += ro.bpf.kver_override=5.4.186


# Keep the requested five-minute boot failure fallback for self-use builds.
PRODUCT_PACKAGES_DEBUG += smg9750-boot-watchdog.sh

# Keep the unused Samsung private security daemons available without autostart.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/rootdir/etc/vaultkeeper_common.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/vaultkeeper_common.rc \
    $(DEVICE_PATH)/rootdir/etc/cass.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/cass.rc

# Route the two RIL wakelock consumers to the platform AIDL implementation.
PRODUCT_PACKAGES += libpower_beyondq

# Preserve user control while granting the installed Google system service LAN discovery.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/configs/default-permissions-smg9750-gms-local-network.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/default-permissions/default-permissions-smg9750-gms-local-network.xml

# Keep the installed Google system packages during data-preserving self-use updates.
$(call inherit-product, device/samsung/beyond2qlte/compat/gapps/gapps.mk)

# Match the installed ih8sn-test2 component and its boot fallback hook.
PRODUCT_PACKAGES += ih8sn-test1
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/compat/ih8sn-test1/ih8sn.conf:$(TARGET_COPY_OUT_SYSTEM)/etc/ih8sn.conf \
    $(DEVICE_PATH)/compat/ih8sn-test1/ih8sn-test-build.txt:$(TARGET_COPY_OUT_SYSTEM)/etc/ih8sn-test-build.txt
