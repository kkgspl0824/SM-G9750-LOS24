# SM-G9750 / beyond2qlte LineageOS 移植源码

三星 Galaxy S10+ 骁龙版 SM-G9750（beyond2qlte）的 LineageOS 24 / Android 17 移植材料，SDK 37，真实内核为 Linux 4.14.190。

## 代码包含什么

| 位置 | 内容 |
| --- | --- |
| [功耗与性能优化增量补丁](patches/los24-power-opt-20261127) | 基于 kk-build 固定清单的 CPU 调频/PowerHint、4 GiB ZRAM、RCU/sched_boost 复位、Wi-Fi 日志精简、cortex-a76 架构属性、power_profile.xml RRO 及 vendor 封包更新。 |
| [kk-build 固定清单](manifests/lineage24-kk-build-20261126-pinned.xml) | 2026-11-26 完整 OTA 使用的 1,250 个源码项目提交。 |
| [kk-build 增量补丁](patches/los24-kk-build-20261126) | 快捷手电筒、蓝牙媒体、cgroup v2 和 Binder 冻结、内核版本后缀及 vendor 封包更新。 |
| [NFC 修订版固定清单](manifests/lineage24-runtimefix8-nfc-pinned.xml) | 旧版 1,249 个源码项目的固定提交。 |
| [patches/los24-runtimefix8-nfc-rebuildfix2](patches/los24-runtimefix8-nfc-rebuildfix2) | 31个项目的完整文本补丁，涵盖设备树、内核、系统框架、HAL、SELinux策略和构建系统；source-index记录删除项及外部二进制变更。 |
| [source/nfc-rebuildfix2](source/nfc-rebuildfix2) | 最新11项重建修复的完整源码覆盖，包括设备配置、内核Makefile、WiFi驱动和Soong处理脚本。 |
| [source/nfc-test1](source/nfc-test1) | NFC标签、指纹显示资源和ih8sn产品接入的源码覆盖。 |
| [source/ih8sn](source/ih8sn) | 固定版本的ih8sn上游源码。 |
| [rebuild工具](rebuild/SM-G9750-LOS24-runtimefix8-nfc-rebuildfix2-20261113/tools) | 固定源码同步、补丁恢复、权限还原、ROM构建、镜像封装及产物校验工具。 |

仓库保存文本源码、补丁、配置和工具；GApps、厂商镜像等预编译载荷通过外部输入接入，对应清单和接入逻辑保留在代码中。旧版源码覆盖、补丁和工具也按版本目录保留。

## 包含的修复与适配

- **内核与新系统兼容**：4.14内核的BPF回移植、旧工具链适配，以及APEX/ext4、垃圾回收和fs-verity能力差异处理。
- **NFC**：补齐`/dev/pn547`设备节点和NXP NFC hwservice的SELinux标签，补齐编译标签文件的安装依赖，并同步Recovery中的标签。
- **指纹与显示**：三星指纹服务桥接、TEE及校准数据只读访问适配，以及`pixel_pitch=48.6`屏下指纹图标比例修正。
- **系统运行**：按真实内核能力处理zygote capability边界，保留沙箱和seccomp；处理TaskPersister尚未创建的最近任务目录，补充Google系统服务局域网发现权限配置。
- **设备服务与启动**：适配旧厂商HAL、电源服务和RIL唤醒锁接口，包含双击唤醒接入、启动失败回退及Recovery保护逻辑。
- **GApps与ih8sn整合**：保留Google服务的产品接入、兼容配置，以及ih8sn组件和开机触发保护。
- **构建可重复性**：固定内核C/汇编路径映射、WiFi编译时钟和模块签名输入，规范化ELF/BTF、PNG与空EROFS镜像的生成元数据。
- **镜像与OTA封装**：统一vendor中的Recovery资源和安装脚本引用，提供运行文件/镜像严格比较、AVB/VINTF、OTA签名及完整数据重建校验。
- **快捷手电筒与蓝牙媒体**：补齐后置手电筒节点访问权限、A2DP 路由和 HIDL 音频服务声明。2026-11-26 版通过手机系统更新器本地安装，蓝牙耳机播放有声。
- **应用冻结**：为 4.14 内核补充 cgroup v2 freezer 和 Binder 冻结接口。已在前一版实测 TikTok 锁屏后自动冻结，2026-11-26 版内核版本为 `4.14.190-kk-build`。
- **功耗与性能调优（2026-11-27）**：释放 `policy0` 300 MHz 最低频并将 `LAUNCH` Hint 缩至 2000ms，优化三簇 `schedutil` 限流与 `pl=0`，ZRAM 扩容至 4 GiB（`lz4`、`page-cluster=0`、`swappiness=100`），开机后关闭 `rcu_expedited`/归零 `sched_boost` 并补充仅限 `not_recovery` 的 `beyondq_sysfs_rcu` SELinux 规则，关闭 Wi-Fi `-dd`/`.logtrace.info` 与残留调试属性，切换 `cortex-a76` 运行时变体并补全 `power_profile.xml` 电量模型。2026-11-27 已通过手机本地 OTA 安装并完成实机回读核验。
