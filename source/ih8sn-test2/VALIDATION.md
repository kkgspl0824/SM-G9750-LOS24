# SM-G9750 指纹图标修复及验证

2026-11-11，在 runtimefix8 + ih8sn-test2 上验证了本次显示修复。该目录保留原 test2 的 ih8sn 组件配置，并在设备覆盖中加入 udfps-pitch-test1 修复；冻结的 runtimefix8 补丁、manifest 和迁移工具保持原样。

## 修复内容

SystemUI 用 `udfps_icon_size / pixel_pitch` 计算指纹图标的像素尺寸。设备未提供 `pixel_pitch` 时，默认值 -1 将 6000 um 图标算成 -6000 px，随后给 210×210 px 的前景视图设置了 3105 px 内边距，表现为白色实心块和黑色横条。

本次仅在设备 `device.mk` 注册 `overlay-product`，新增浮点资源 `pixel_pitch=48.6`。该参数来自 beyond2qlte 实际构建使用的 S6E3HA9_AMB644WF01 面板：69.984 mm / 1440 px 与 147.744 mm / 3040 px 都等于 48.6 um/px。面板 DTS 的整数物理尺寸 70×148 mm 是取整值，不能用逻辑密度560替代像素间距。

源码依据为固定内核提交 `d1d9579baf3fc993b91d8ee22227fbb50464c8b4` 的 [beyond2qlte display DTS](https://github.com/sm8150-samsung/android_kernel_samsung_sm8150-common/blob/d1d9579baf3fc993b91d8ee22227fbb50464c8b4/arch/arm64/boot/dts/samsung/sm8150-sec-beyond2qlte-display-r00.dtsi) 与 [面板配置](https://github.com/sm8150-samsung/android_kernel_samsung_sm8150-common/blob/d1d9579baf3fc993b91d8ee22227fbb50464c8b4/drivers/gpu/drm/msm/samsung/S6E3HA9_AMB644WF01/dsi_panel_S6E3HA9_AMB644WF01_wqhd_octa_cmd.dtsi)。保存的面板配置已与冻结工作树逐字节核对。

## 已完成的验证

- 原生 aapt2 编译/链接、签名通过。原有24项产品覆盖资源、Manifest和证书保持，仅新增 pixel_pitch；图标原生计算尺寸为123 px，内边距43 px。
- 在已验证的 test2 target-files 上重建 system/vbmeta 和完整 OTA，未重新整编 Android 全源码。10,331项运行文件/镜像审计只允许产品覆盖APK及生成的system/vbmeta变化；其余运行文件、权限及boot/Recovery/vendor/DTBO保持。原生文件/AVB、VINTF、签名、ZIP CRC和system/vendor块载荷重建通过，原37条OTA安装保护断言保持。
- 保留数据安装后，Recovery实际状态0，六分区完整回读通过，data UUID保持；Recovery同字节随OTA写入，vbmeta不写。录入指纹和应用清单保持，原PIN与一次真实指纹认证通过。普通ADB UID2000、文件加密、SELinux Enforcing保持，观察至uptime415.28秒无重启，所检查致命异常、ANR和crash缓冲均为0。

| 实际活动显示模式 | 缩放 | 实际内边距 | 亮屏指纹纹路 | AOD显示 | 真实AOD指纹解锁 |
| --- | --- | --- | --- | --- | --- |
| 1440×3040 | 1.0 | 43 px | 完整 | 正常 | 通过 |
| 1080×2280 | 0.75 | 32 px | 完整 | 正常 | 通过 |
| 720×1520 | 0.5 | 21 px | 完整 | 与充电文字重叠 | 通过 |

三档均通过系统临时显示模式接口切换实际活动模式，密度保持560，未用 `wm size` 模拟。AOD显示由截图、Doze状态和用户面板观察共同确认；真实认证由用户手指操作，三次成功计数独立增加。电脑注入休眠/唤醒仅用于准备界面，不当作物理输入认证证据。

720p AOD 的指纹容器和提示区布局范围有14 px垂直交叠；用户确认存在重叠、解锁正常，并明确接受其作为不影响使用的边界现象。本次不追加布局修复，也不将720p显示项记为无重叠。未测长期AOD耗电、防烧屏行为或大量反复切换的稳定性。

测试结束恢复1440×3040/60 Hz、密度560、AOD关闭和原显示模式偏好；secure/system/global设置逐项与测试前一致，同一boot ID、普通ADB和Enforcing保持。

## 测试产物身份

- ROM：`lineage-24.0-20261111-UNOFFICIAL-beyond2qlte-runtimefix8-ih8sn-test2-udfps-test1.zip`
- ROM SHA256：`f1eac845a1880f332af3fa1b8da33232d61b7f8d41f6e25a9708909acff26dbe`
- 配套 target-files SHA256：`13c6cb668ac4f035c55a299ae83b35d123f7f4cb325b789e6286a9c96b6f2ba0`
- 产品覆盖 APK SHA256：`35e4d6fab1c611c357714668687ec22c0edfb4d98cdea1f92431201e529d9d59`

ROM沿用原test2的build.prop和ih8sn标记，以上哈希及实际覆盖资源用于识别测试包。ROM、target-files、签名私钥、完整日志、截图、应用清单、UUID和指纹dump不纳入本仓库。

## 后续源码使用

先在新的空工作区用完整迁移资料恢复 runtimefix8，再合入本目录的设备覆盖，并按固定 ih8sn 源码构建缺省忽略的ELF。`device.mk` 包含原 test2 的接入，需与新增的 `overlay-product` 一起使用；有后续修改的工作区应合并对应行，不直接覆盖整个文件。

仓库内冻结的 runtimefix8 比较工具仍要求原载荷一致。本次是独立新版本，不能修改旧校验清单或放宽比较来把新载荷标成冻结基线。仅 clone 本仓库仍不足以重建完整ROM，构建输入边界见根目录README。
