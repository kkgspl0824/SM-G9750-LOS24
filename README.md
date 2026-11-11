# SM-G9750 / beyond2qlte 源码移植记录

本仓库仅保存骁龙版三星 SM-G9750 的 LOS24 文本源码修改、固定源码版本和构建脚本。基线为 LineageOS 24.0 / Android 17 / SDK 37、真实内核 4.14.190；目录名 Android16 是历史名称。

## 跟踪范围

- `manifests/lineage24-runtimefix8-pinned.xml`：runtimefix8 的 1,249 项目固定提交。
- `patches/los24-runtimefix8/`：29 项目的文本源码补丁，保留源码删除操作；`source-index.json` 记录项目基准、导出补丁 SHA256、15 项删除和排除的 13 项二进制变更。
- `rebuild/SM-G9750-LOS24-runtimefix8-20261110/tools/`：冻结迁移包的原同步、还原、构建和产物比较脚本（含 Repo Python launcher），保持原文件和路径。
- `source/ih8sn/`：固定上游提交的源码与原构建配置，来源见其中的 `UPSTREAM.md`。
- `source/ih8sn-test2/`：独立实验的设备配置覆盖，使用 test2 的 rc、配置及版本标记，并包含已实测的 udfps-pitch-test1 像素间距修复；不改写 runtimefix8 基线。该目录中的 `device.mk` 是设备文件的完整覆盖副本。

`source-review/`、历史补丁、日志、手机数据、环境记录、ROM、镜像、APK/JAR/ELF、签名私钥、工具二进制和完整迁移包均忽略。忽略规则不会删除本机文件。新增顶层目录默认忽略，需要明确开放后才跟踪。

## 构建边界

这是源码修改仓库，不是完整 Android 源码镜像，也不是可独立构建的完整迁移包。补丁以各项目固定提交为基准，纯文本补丁排除了 GApps、专有库等二进制变更。原构建脚本仍要求完整迁移包中的原始补丁、元数据、GApps 和 vendor 输入；仅 clone 本仓库无法直接运行全套构建。不要用这些导出补丁覆盖冻结迁移包或修改其校验清单。

本机完整复现入口仍为 `rebuild/SM-G9750-LOS24-runtimefix8-20261110/README.md`（不入 Git），完整迁移包需另行保管。基础源码按固定 manifest 获取；只在新工作区恢复，不对现有修改树执行强制同步。

ih8sn-test2 是独立实验，软件属性不代表真实 Bootloader 锁定或硬件认证。设备配置引用的 `ih8sn` ELF 已忽略，需要由固定上游源码另行构建；未将该实验合入冻结 runtimefix8。各源码和外部输入沿用其原有许可。

## 指纹图标验证

本机型产品覆盖设置 `pixel_pitch=48.6`，修复默认负值造成的指纹图标异常。1440p、1080p锁屏/AOD显示与真实AOD解锁已通过；720p的充电文字重叠作为用户接受的边界现象保留，解锁正常。测试后已恢复原显示和AOD设置。构建、安装、各分辨率验证边界及产物哈希见 [验证摘要](source/ih8sn-test2/VALIDATION.md)。

## Git 仓库

远程仓库：https://github.com/kkgspl0824/SM-G9750-LOS24 ，主分支为 `main`。

```sh
git clone https://github.com/kkgspl0824/SM-G9750-LOS24.git
```

完整迁移包及二进制输入不随 Git 上传，需单独保管。
