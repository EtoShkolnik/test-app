[app]
title = TOTP Generator
package.name = totpgenerator
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,pyotp
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2

android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
