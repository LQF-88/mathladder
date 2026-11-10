# Android 构建与发布指南

## 0. 准备

- 先把 `buildozer.spec` 里的 `package.domain` 改成你控制的域名，例如 `io.github.yourname`。
  最终应用 ID 是 `<package.domain>.<package.name>`，默认值为
  `org.mathladder.mathladder`。**应用一旦上传 Google Play，ID 不能修改。**
- 同时修改 `title`（桌面图标下的名称）、`version`、`android.version_code`，
  并保持 `app/app.py` 中 `MathLadderApp.VERSION` 与 `version` 一致。
- `android.version_code` 每次上传商店都必须比上一版大。

当前配置：

| 项目 | 值 |
| --- | --- |
| 目标 SDK | API 35 |
| 最低 SDK | API 24（Android 7.0） |
| NDK | r28c（支持 16 KB 内存页） |
| Python / Kivy | 3.11.7 / 2.3.2 |
| python-for-android | v2026.05.09 |
| 架构 | arm64-v8a + armeabi-v7a |
| 输出 | debug 为 APK；release 为 AAB |
| 权限 | 无 |
| 包体 | 字体约 17 MB，APK 约 40–60 MB |

> Android 15 及以上的部分设备使用 16 KB 内存页。目标 SDK 35 的应用必须让
> 所有 64 位原生库按 16 KB 对齐，否则会安装成功但启动即闪退。NDK r28 默认
> 生成 16 KB 对齐的库，CI 会用 `tools/check_apk_alignment.py` 自动校验。

## 1. 用 GitHub Actions 构建调试 APK

`.github/workflows/android.yml` 会在 push、PR 和手动触发时运行：

1. 运行 `pytest` 与 `ruff check`。
2. 在 Ubuntu 22.04 + JDK 17 上安装 Buildozer 和 Android 工具链。
3. 缓存 `~/.buildozer` 与 `~/.android`，执行 `buildozer -v android debug`。
4. 运行 `tools/check_apk_alignment.py`，确认 64 位原生库支持 16 KB 页。
5. 上传 `mathladder-debug-apk` 工件（保留 30 天）。
6. 如果触发的是 `v*` 标签，自动创建 GitHub Release 并附加 APK。

安装调试包：

```bash
adb install -r mathladder-1.0.1-arm64-v8a_armeabi-v7a-debug.apk
```

没有 adb 时，把 APK 传到手机，允许“安装未知来源应用”后点击安装。

> 每次 CI 首次构建会生成新的 Android 调试签名。如果覆盖安装时提示“应用未安装”
> 或“签名不一致”，先在手机上卸载旧版 MathLadder，再安装新的 APK。

## 2. 生成签名密钥

只需做一次，务必离线备份密钥和密码。丢失密钥后将无法更新已上架应用。

```bash
keytool -genkey -v \
  -keystore release.keystore \
  -alias mathladder \
  -keyalg RSA -keysize 2048 -validity 10000

# macOS 上复制 base64 到剪贴板
base64 -i release.keystore | pbcopy
# Linux
base64 -w 0 release.keystore
```

在 GitHub 仓库 **Settings → Secrets and variables → Actions** 添加：

| Secret | 内容 |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | `release.keystore` 的 base64 |
| `ANDROID_KEYSTORE_PASSWORD` | keystore 密码 |
| `ANDROID_KEY_ALIAS` | `mathladder` |
| `ANDROID_KEY_PASSWORD` | key 密码 |

不要把 `release.keystore` 提交到仓库；`.gitignore` 已忽略它。

## 3. 构建签名的 AAB / APK

打开 **Actions → Signed Android release → Run workflow**：

- `artifact = aab`：上传 Google Play 用的签名 AAB。
- `artifact = apk`：生成可直接安装的签名 APK。

工作流会把密钥解码到临时文件、写入 `buildozer.spec`、构建完成后删除密钥。
产物在运行页底部的 `mathladder-signed-*` 工件中。

本地构建（Linux / WSL2）：

```bash
# 在 buildozer.spec 中填好 android.keystore 等四项
buildozer -v android release
ls -lh bin/
```

## 4. 发布到 Google Play

1. 注册 Google Play 开发者账号，创建应用。
2. **Testing → Internal testing** 上传第一个 AAB，添加测试人员，确认安装与启动正常。
3. 补齐商店资料：
   - 应用名称：数学阶梯（或你修改后的名称）
   - 简短说明：离线数学练习，16 个阶段、88 个题型，无限自动出题
   - 完整说明：可直接参考 README 的功能与课程范围；不要使用 Kumon 名称或教材图片
   - 截图：使用 `docs/screenshots/`，或按 Play 要求重新截取（至少 2 张）
   - 应用图标：`app/assets/icons/icon-512.png`（512×512）
   - 特色图片：需要另行制作 1024×500
4. 填写 **Data safety**：不收集、不共享数据，无网络传输，卸载即删除。
5. 填写 **内容分级** 问卷；本应用不含广告、内购、用户生成内容。
6. 提供隐私政策 URL（可把 README 的“数据与隐私”一节发布为静态页面）。
7. 先走 Internal testing → Closed testing → Production。

Google Play 对新个人开发者账号有测试人数和时长要求，具体以 Play Console 当前政策为准。

## 5. 版本发布清单

- [ ] 修改 `buildozer.spec`：`version`、`android.version_code`
- [ ] 修改 `app/app.py`：`VERSION`
- [ ] 更新 `README.md` / 商店说明中的变更
- [ ] `pytest` 与 `ruff check` 通过
- [ ] 在真机上验证做题、返回键、旋转/暂停、卸载重装
- [ ] 构建签名 AAB 并上传 Internal testing
- [ ] 打标签并推送：`git tag v1.0.1 && git push origin v1.0.1`
- [ ] 在 GitHub Release 中补充更新说明

## 6. 常见问题

**构建卡在下载 SDK/NDK**
Buildozer 首次构建会下载数 GB 文件。GitHub Actions 已缓存 `~/.buildozer`；
本地构建请保证网络稳定并预留磁盘空间。

**`libtinfo5` 安装失败**
较新的 Ubuntu 可能已移除该包。可以删除该依赖重试；它是部分 NDK 工具链的可选依赖。

**APK 体积过大**
字体是主要体积来源。如果只需要简体中文，可对 Noto Sans SC 做子集化，或删除 Bold 字重后
同步修改 `app/theme.py` 中的字体注册。

**安装后闪退**
先确认手机不是 16 KB 内存页设备：连接 USB 并开启调试后运行

```bash
adb logcat -d | grep -E 'FATAL EXCEPTION|UnsatisfiedLinkError|16 KB|python'
```

如果日志出现 `UnsatisfiedLinkError`、`alignment` 或 `16 KB`，说明原生库没有按
16 KB 对齐。当前配置使用 NDK r28c，CI 构建时会运行
`python tools/check_apk_alignment.py bin/*.apk`；本地构建请确认 `android.ndk = 28c`
且没有沿用旧的 `.buildozer` 缓存（删除 `.buildozer` 后重建）。

其他 Python 异常可用 `adb logcat | grep -i python` 查看。确认
`source.include_exts` 包含 `otf`、`wav`，且 `app/assets/` 已打进包内。也可以把
`android.archs` 暂时设为 `arm64-v8a` 后重新构建排查。

**Play Console 提示 target SDK 过低**
提高 `android.api`，并确认 python-for-android / Buildozer 版本支持对应 SDK。
