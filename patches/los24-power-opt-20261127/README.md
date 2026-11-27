# LOS24 Power Optimization Patch Set (`los24-power-opt-20261127`)

本目录保存 `sm-g9750-lineage24-power-opt-20261127` 相对 [los24-kk-build-20261126](../los24-kk-build-20261126/README.md) 的增量源码补丁与封包扩展清单，不含私钥、密码、设备序列号或个人数据。

## 文件清单

- [device-samsung-beyond2qlte.patch](device-samsung-beyond2qlte.patch)：增量新增 `overlay-product/frameworks/base/core/res/res/xml/power_profile.xml` 与 `rootdir/vendor-opt/` 下的 9 项 vendor 配置覆盖（`init.qcom.post_boot.sh`、`powerhint.json`、`fstab.ramplus`、`init.ramplus.rc`、`init.beyond2q.rc`、`android.hardware.wifi.supplicant-service.rc`、`wifi_brcm.rc`、`default.prop`、`build.prop`）。
- [device-samsung-sm8150-common.patch](device-samsung-sm8150-common.patch)：在 `los24-kk-build-20261126` 之后增量追加 `beyondq_sysfs_rcu` SELinux 标签与 `vendor_init` 写权限（`/sys/kernel/rcu_expedited`、`/sys/kernel/rcu_normal`），包裹在 `not_recovery(...)` 中。
- [finalize-target-files.patch](finalize-target-files.patch)：基于冻结包 `finalize-target-files.py` 的封包补丁，保留 `kk-build` 媒体/SELinux/VINTF 注入并新增 `rootdir/vendor-opt/` 9 项文件的内容断言、`debugfs` 注入与镜像回读校验。
- [vendor-files.txt](vendor-files.txt)：从 Soong vendor 构建产物读取并核对的 11 项生成文件清单。
- [source-index.json](source-index.json)：项目提交、增量补丁校验值与产物哈希索引。

## 说明

- `kernel/samsung/sm8150-common` 相对 `20261126` 基线无净改动；Attempt 1 曾尝试开启 `CONFIG_ARM64_LSE_ATOMICS=y`，触发 `spinlock.o` `.org backwards` 编译失败并已完整回退。
- 本增量包对应构建产物 `artifacts/sm-g9750-lineage24-power-opt-20261127/lineage-24.0-20261127-UNOFFICIAL-beyond2qlte.zip`（SHA-256 `28941be2692e1a2fa1226fd13e2a0215c66b5508d4a96634fde6d7b6909ac285`）。该包已于 2026-11-27 在 SM-G9750 通过本地 OTA 安装，10 项抽检文件哈希与运行态内核/vendor/RRO 调优参数均通过实机回读验证。
