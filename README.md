# SM-G9750 / beyond2qlte 源码移植记录

本仓库保存骁龙版三星 SM-G9750 的 LOS24 文本源码、固定版本和重建工具。当前合并版为 runtimefix8 + ih8sn-test2 + udfps-test1 + nfc-test1，Android17 / SDK37，真实内核 4.14.190；目录名 Android16 是历史名称。

## 当前材料

- `manifests/lineage24-runtimefix8-nfc-pinned.xml`：1249 项目固定提交，与原基线相同；合并变化由完整补丁记录。
- `patches/los24-runtimefix8-nfc/`：29 项目的完整文本补丁和 source-index，保留 15 项删除；14 项二进制变更明确另列并保存在完整重建包。
- `source/nfc-test1/`：本次实际合并的八项文本源码覆盖，包含 NFC 精确标签、ih8sn-test2 接入/启动保护和指纹像素间距。文件是完整副本，有其他改动的树应合并对应行；`source-index.json` 保存精确哈希、权限和外部输入要求。
- `source/ih8sn/`：固定上游源码，来源见 UPSTREAM.md；已验收的静态 ELF 在完整资料包中，不纳入 Git。
- `rebuild/SM-G9750-LOS24-runtimefix8-nfc-20261111/tools/`：新资料的同步、恢复、构建与严格产物比较工具。旧 runtimefix8 补丁、manifest、工具与 source/ih8sn-test2 目录保留。

多个版本的补丁是各自相对固定 HEAD 的完整集合，不能按目录顺序叠加。恢复工具只用于新的空工作区，不覆盖已有修改。

## 完整重建资料

本机入口为 `rebuild/SM-G9750-LOS24-runtimefix8-nfc-20261111/README.md`，配套压缩包 `SM-G9750-LOS24-runtimefix8-nfc-20261111.tar.gz`，1,692,749,316 字节，SHA256 `644bb440fe595bfd1dbaa0cbd08c3e88c6d515b62196dd8415a2553a82cd07dd`。

完整包保存 29 项目完整二进制补丁、1036 个变更文件、15 项删除和匹配 NFC 的两个 vendor 输入，含 GApps、静态 ELF、签名配置及权限/链接清单。Git 中只保留文本审阅材料和工具，忽略 ROM、镜像、APK/JAR/ELF、签名私钥、完整包、日志和手机私有数据；**仅 clone 本仓库仍不足以构建完整 ROM**。当前旧 vendor-runtimefix7 不能替代新的 NFC 输入。

服务器实际工作源码已合并，完整补丁从固定 HEAD 重放、内容/权限/链接/删除项及新旧载荷正反例检查通过。本轮没有重新全量编译 Android、第二台机器整编或再次刷机。新构建工具继续严格比较 10323 个运行文件和 8 项镜像/映射，差异会停止出包，不放宽旧校验清单。

## 实机验证范围

参考 ROM SHA256 `b9a0a4cb89ba940b0bad2e1fd3148dca9edea64ee9b76b03efb9801c9f9a159d`。此前已保留数据安装，六分区回读、原 PIN 解锁、2 条指纹和 24 个第三方应用保持，NFC 初始化与开关循环通过，相关 SELinux 拒绝为 0。没有测试卡，实体读卡、天线、eSE/HCE 和支付认证未验收，见 [NFC 验证摘要](source/nfc-test1/VALIDATION.md)。ih8sn 软件属性不代表真实 Bootloader 锁定或硬件认证。

指纹图标修复保留 `pixel_pitch=48.6`。此前 1440p、1080p 的锁屏/AOD 显示和真实 AOD 解锁已通过；720p 文字重叠作为用户接受的边界现象保留，见 [先前指纹验证](source/ih8sn-test2/VALIDATION.md)。本轮源码合并不扩展这些验收结论。

## Git 仓库

远程仓库：https://github.com/kkgspl0824/SM-G9750-LOS24 ，主分支为 `main`。

```sh
git clone https://github.com/kkgspl0824/SM-G9750-LOS24.git
```

完整迁移包及二进制输入不随 Git 上传，需单独保管。
