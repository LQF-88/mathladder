[app]

# Android application label. ASCII keeps aapt happy on every SDK version;
# change it to "数学阶梯" if you prefer a Chinese home-screen label.
title = MathLadder

# Change package.domain to a domain you control before publishing.
# The final application id is <package.domain>.<package.name>.
package.name = mathladder
package.domain = org.mathladder

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,wav,ogg,json,txt
source.include_patterns = app/assets/*
source.exclude_dirs = tests,tools,docs,.github,.venv,__pycache__,bin,build,dist,.pytest_cache,.ruff_cache
source.exclude_patterns = *.pyc,*.pyo,*.md,*.pdf,*.zip,.DS_Store

version = 1.0.1

# Keep these aligned with app/app.py (MathLadderApp.VERSION).
# Python is pinned to 3.11 because Kivy 2.3.2 is best tested there and the
# 3.14 hostpython bundled by newer p4a releases ships a broken pip that
# cannot bootstrap the build virtualenv.
requirements = python3==3.11.7,kivy==2.3.2
orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/app/assets/icons/icon-512.png
presplash.filename = %(source.dir)s/app/assets/icons/splash.png
android.presplash_color = #FBF3E4

android.api = 35
android.minapi = 24
# NDK r28 links every shared library with 16 KB-aligned load segments.
# Android 15+ devices may use 16 KB memory pages; libraries built with
# NDK r25b are only 4 KB-aligned and crash at launch there.
android.ndk = 28c
android.ndk_api = 24
android.accept_sdk_license = True

# Fully offline app: no runtime permissions are required.
android.permissions =
android.private_storage = True
android.allow_backup = False

android.archs = arm64-v8a, armeabi-v7a
android.release_artifact = aab
android.debug_artifact = apk
android.version_code = 2

# Signing values are filled in by .github/workflows/android-release.yml
# (or by you locally) before `buildozer android release`.
android.keystore =
android.keystore_passwd =
android.keyalias =
android.keyalias_passwd =

p4a.bootstrap = sdl2
# v2026.05.09 supports NDK r28 (16 KB page sizes). The Python version is
# pinned in `requirements` above, so this release still builds Python 3.11.
p4a.branch = v2026.05.09
