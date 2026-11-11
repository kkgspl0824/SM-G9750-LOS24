# NFC 合并源码与验收范围

本目录是当前 nfc-test1 的八项文本源码覆盖，包含 NFC 两条精确标签、ih8sn-test2 产品接入/启动保护和 UDFPS 48.6 像素间距。设备与 common 文件均为完整覆盖副本；只合并对应行到已有修改的树，不盲目覆盖。`source-index.json` 记录内容和精确权限。

`compat/ih8sn-test1/ih8sn` 静态 ELF 不进入 Git，准确哈希保存在 source-index；完整重建资料已包含该已验收二进制。固定上游源保留于 `../ih8sn/`，单独重编组件需要原 NDK r27b / arm64 API35 环境。直接恢复完整资料不依赖旧实验目录或 NDK。

NFC 修复为 `/dev/pn547 -> nfc_device` 和 `vendor.nxp.nxpnfc::INxpNfc -> hal_nfc_hwservice`，没有增加 TE 许可或 permissive 域。必须同时使用完整新资料中的匹配 vendor 镜像与 vendor 子包；旧 vendor-runtimefix7 输入缺少这些标签。

参考 ROM SHA256：`b9a0a4cb89ba940b0bad2e1fd3148dca9edea64ee9b76b03efb9801c9f9a159d`。此前已保留数据安装，Recovery 状态 0、六分区回读通过，原 PIN、两条指纹和 24 个第三方应用保持。NFC 初始化、开关循环和短时启动稳定性通过，相关 SELinux 拒绝为 0。没有测试卡，实体读卡、天线、eSE/HCE 和支付认证未验收。

本轮合并了服务器实际工作源码，并对完整重建资料的 29 项目补丁、1036 文件、15 删除逐项重放和验证；当前 NFC 载荷比对通过，缺少 NFC 的旧包被拒绝。未进行 Android 全量整编、第二台机器整编或再次刷机。旧 runtimefix8 和 ih8sn-test2 目录保留。

完整入口：`rebuild/SM-G9750-LOS24-runtimefix8-nfc-20261111/README.md`。Git 中的 `patches/los24-runtimefix8-nfc/` 是基于固定 HEAD 的完整文本补丁；14 项二进制变更另列，不替代完整包的必要输入。仅 clone 仓库仍不能直接重建 ROM。
