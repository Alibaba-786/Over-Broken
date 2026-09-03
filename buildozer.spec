[app]
title = Royal Casino USDT
package.name = royalcasinousdt
package.domain = org.royalcasino
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# Guaranteed Stable Requirements for Kivy Android SSL API
requirements = python3,kivy==2.2.1,openssl,hostpython3

orientation = portrait
fullscreen = 0

# Android SDK & API Configurations
android.permissions = INTERNET, ACCESS_NETWORK_STATE
android.accept_sdk_license = True
android.api = 31
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1


