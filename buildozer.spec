[app]
title = Royal Casino USDT
package.name = royalcasinousdt
package.domain = org.royalcasino
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

requirements = python3,kivy==2.2.1,openssl,requests,urllib3,certifi,hostpython3

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, ACCESS_NETWORK_STATE
android.accept_sdk_license = True
android.api = 33
android.minapi = 21
android.ndk = 25b
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
