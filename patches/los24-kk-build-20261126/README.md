# SM-G9750 LOS24 kk-build 增量补丁

这组补丁用于 2026-11-26 的完整 OTA。上游 `lineage-24.0` 清单提交为 `913c6baa35ffa32be9ae33368cac69dbec6ead4b`。[固定项目清单](../../manifests/lineage24-kk-build-20261126-pinned.xml)

## 应用顺序

在固定项目清单对应的源码树上，先恢复 [NFC 重建修订 2 基础补丁](../los24-runtimefix8-nfc-rebuildfix2)及其构建输入。再按 [source-index.json](source-index.json) 的顺序，在对应 Git 项目根目录应用以下补丁。固定清单记录的提交是应用基础补丁前的 HEAD。

| 项目 | 补丁 | 改动 |
| --- | --- | --- |
| `device/samsung/beyond2qlte` | [device-samsung-beyond2qlte.patch](device-samsung-beyond2qlte.patch) | 增加的软件 A2DP 路由使用现有蓝牙 HAL，补齐后置手电筒节点的属主和权限。 |
| `device/samsung/beyond2qlte` | [bluetooth-audio-manifest.patch](bluetooth-audio-manifest.patch) | 在设备 VINTF 清单声明现有 HIDL 2.0 蓝牙音频 provider。 |
| `device/samsung/sm8150-common` | [device-samsung-sm8150-common.patch](device-samsung-sm8150-common.patch) | 加入手电筒节点标签，并给相机 HAL 开放该节点的必要访问。 |
| `device/samsung/sm8150-common` | [guard-recovery.patch](guard-recovery.patch) | 将手电筒规则和 genfs 标签限定在正常 Android 的策略。 |
| `kernel/samsung/sm8150-common` | [kernel414-cgroup-v2-binder-freezer.patch](kernel414-cgroup-v2-binder-freezer.patch) | 回移植 cgroup v2 freezer 和 Binder 冻结。 |
| `kernel/samsung/sm8150-common` | [kernel414-kk-build-localversion.patch](kernel414-kk-build-localversion.patch) | 定义 `-kk-build` 并关闭自动 Git 版本后缀。 |
| `device/samsung/beyond2qlte` | [device-kk-build-localversion.patch](device-kk-build-localversion.patch) | 传入空的 `LOCALVERSION` 参数，避免内核版本尾部出现 `+`。 |

## Vendor 封包

产品使用预编译 vendor 镜像作为种子。构建 `target-files-package` 时，需同时生成 [vendor-files.txt](vendor-files.txt) 所列的安装目标。这些路径相对于 `out/target/product/beyond2qlte/vendor/`。

把基础版本的 `finalize-target-files.py` 复制到单独的构建目录，在该目录对副本应用 [finalize-target-files.patch](finalize-target-files.patch)。打包时设置 `SMG9750_BASELINE_KIT` 为冻结资料目录、`SMG9750_VENDOR_FILES` 为上述清单的绝对路径，并沿用本次构建的 `BUILD_DATETIME`。按原参数运行修改后的脚本，输入原生 target-files，生成最终 target-files 和验证报告，再生成 OTA。脚本同步生成的 Recovery、媒体策略、SELinux 和 VINTF 声明到 vendor 镜像，保留原文件的权限和标签并重算 AVB。

完整构建需要冻结资料中的厂商载荷、GApps、二进制补丁和签名输入。

## 验证范围

2026-11-26 完整 OTA 已用系统更新器在 SM-G9750 本地安装。设备回读的内核版本为 `4.14.190-kk-build`。用户确认 Baseus Bowie W04 耳机播放有声，日志显示 HIDL A2DP 会话成功启动，并被选为媒体输出。
