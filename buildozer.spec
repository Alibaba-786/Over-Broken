[app]
title = Royal Casino USDT
package.name = royalcasinousdt
package.domain = org.royalcasino
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# Fixed C-bindings and urllib compilation for Android NDK
requirements = python3,kivy==2.3.0,openssl,urllib3,certifi,hostpython3

orientation = portrait
fullscreen = 0

# Android SDK / Permissions
android.permissions = INTERNET, ACCESS_NETWORK_STATE
android.accept_sdk_license = True
android.api = 33
android.minapi = 21
android.ndk_api = 21
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1

