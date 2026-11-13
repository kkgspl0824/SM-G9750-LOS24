# SM-G9750 / beyond2qlte 源码移植记录

本仓库保存骁龙版三星 SM-G9750 的 LOS24 文本源码、固定版本和重建工具。当前源码和重建资料为 runtimefix8 + GApps + ih8sn-test2 + udfps-test1 + nfc-rebuildfix2，Android17 / SDK37，真实内核 4.14.190；目录名 Android16 是历史名称。新版本已通过独立完整冷构建验收，尚未刷机。

## 当前材料

- `manifests/lineage24-runtimefix8-nfc-pinned.xml`：1249 项目固定提交，与原基线相同；合并变化由完整补丁记录。
- `patches/los24-runtimefix8-nfc-rebuildfix2/`：31 项目的完整文本补丁和 source-index，包含原移植及 NFC 修复，保留 15 项删除；14 项二进制变更明确另列并保存在完整重建包。
- `source/nfc-rebuildfix2/`：本次实际合并的 11 项源码覆盖，用于安装依赖、内核路径/时间/签名输入及生成元数据的可重复构建。文件为完整副本，有其他修改的树应合并对应行；`source-index.json` 保存精确哈希、权限和外部输入要求。完整移植变化以31项目补丁及完整资料为准。
- `source/ih8sn/`：固定上游源码，来源见 UPSTREAM.md；已验收的静态 ELF 在完整资料包中，不纳入 Git。
- `rebuild/SM-G9750-LOS24-runtimefix8-nfc-rebuildfix2-20261113/tools/`：同步、恢复、构建、vendor/Recovery封装与严格比较工具。旧 runtimefix8、nfc-test1 补丁/源码/工具均冻结保留。

多个版本的补丁是各自相对固定 HEAD 的完整集合，不能按目录顺序叠加。恢复工具只用于新的空工作区，不覆盖已有修改。

## 完整重建资料

本机入口为 `rebuild/SM-G9750-LOS24-runtimefix8-nfc-rebuildfix2-20261113/README.md`，配套压缩包 `SM-G9750-LOS24-runtimefix8-nfc-rebuildfix2-20261113.tar.gz`，1,695,407,292 字节，SHA256 `9f0f9fe67706a6805fe3e5b320fbf28a738236f3e3eadffa48aabb729400c6a3`。校验归档后保留权限解压（例如GNU tar的`-xpf`），再核对内部`SHA256SUMS`。

完整包固定1249项目，保存31项目完整二进制补丁、1044个变更文件、15项删除、两个NFC vendor种子输入及固定内核模块签名输入，含GApps、静态ELF和权限/链接清单。基础Android/LineageOS源码由同步脚本联网获取。Git只保存文本和工具，忽略ROM、镜像、APK/JAR/ELF、私钥、完整包及私人日志；**仅clone本仓库仍不足以重建ROM**。完整归档含受限内核私钥，须以0600保存，不公开分发；旧vendor-runtimefix7不能替代NFC种子输入。

旧包全部26项载荷变化已审计，无新增/丢失成员，随后建立新基线。2026-11-13第二轮从物理独立源码树重放完整资料，空out/ccache/tmp，执行最终构建入口并真实退出0：10323个运行文件和8项镜像/映射零差异，文件/AVB、VINTF、OTA签名及system/vendor完整数据重建均通过。两份ROM ZIP也完全相同，1831540116字节，SHA256 `530016d7eaae9b83cac2565c1cc3341d6b685c8744de5e9d86bcba552e312e68`。target-files的其余24项载荷也相同，所检查的ZIP成员属性差异为META/vbmeta_digest.txt封装时间戳；不宣称target-files ZIP整体字节相同。

服务器活动源码已合并11项修复和两个vendor相对链接，完整校验通过，31项目HEAD/index保持。新契约自比对及旧包/单NFC标签删除负例通过，旧资料和契约未放宽。128项归档文件读回校验通过，最终构建核心与实测输入的内容/权限/大小一致。详见[源码与验收摘要](source/nfc-rebuildfix2/VALIDATION.md)。本次为同服务器独立工作区，尚未在另一台机器重新联网同步整编。前轮失败记录保留在本机notes中。

## 实机验证范围

新ROM未安装或实机测试。新内核保持强制模块签名，但固定证书与旧ROM不同；私钥只在完整资料inputs中，ROM无外置模块，外置模块兼容未验收。

旧实机验收ROM SHA256 `b9a0a4cb89ba940b0bad2e1fd3148dca9edea64ee9b76b03efb9801c9f9a159d`。此前保留数据安装、六分区回读、原PIN解锁、2条指纹和24个第三方应用保持，NFC初始化/开关循环通过，相关SELinux拒绝为0。没有测试卡，实体读卡、天线、eSE/HCE与支付未验收，见[NFC验证摘要](source/nfc-test1/VALIDATION.md)。这些是历史结果；ih8sn软件属性不代表真实Bootloader锁定或硬件认证。

指纹图标修复保留 `pixel_pitch=48.6`。此前 1440p、1080p 的锁屏/AOD 显示和真实 AOD 解锁已通过；720p 文字重叠作为用户接受的边界现象保留，见 [先前指纹验证](source/ih8sn-test2/VALIDATION.md)。本轮源码合并不扩展这些验收结论。

## Git 仓库

远程仓库：[SM-G9750-LOS24](https://github.com/kkgspl0824/SM-G9750-LOS24)，主分支为`main`。

```sh
git clone https://github.com/kkgspl0824/SM-G9750-LOS24.git
```

完整迁移包及二进制输入不随 Git 上传，需单独保管。
