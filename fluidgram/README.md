# FluidGram — v0.1-alpha1
Unofficial open-source Telegram Android overlay for OnePlus 15 / ColorOS 17.

This branch holds the prototype in fluidgram/ rather than modifying the unrelated repository's main branch. Upstream Telegram Android sources are cloned only when compiling and pinned to commit 3de37c8cfb039452be7398909461da6288babf15 (13.1.1).

Stage 1:
- separate Android package dev.fluidgram.oneplus15.web
- original circular icon, unofficial app label
- cool-white start screen
- camera flip motion 580 ms -> 440 ms and custom interpolator
- camera-flip in-progress guard and 560 ms debounce, preventing overlapping requests
- latest upstream Camera2 implementation preserved; no forced 60 FPS
- official-only passkeys and auto update check disabled

NOT YET TESTED: no APK built or OnePlus 15 hardware validation; no proven fix for camera sync or green frames. Full ColorOS theme and chat transitions remain later work.

Build: GitHub Actions > FluidGram Android APK (OnePlus 15). No APK is produced before secrets exist. Create a dedicated public GitHub repository for this source before putting credentials into GitHub. Required secrets:
FLUIDGRAM_API_ID, FLUIDGRAM_API_HASH, FLUIDGRAM_GOOGLE_SERVICES_JSON_B64, FLUIDGRAM_KEYSTORE_B64, FLUIDGRAM_KEY_ALIAS, FLUIDGRAM_STORE_PASSWORD, FLUIDGRAM_KEY_PASSWORD.

API credentials from https://my.telegram.org. Firebase google-services.json must include application dev.fluidgram.oneplus15.web. Use a persistent private signing keystore; never commit keys. Toolchain: Android SDK 36; Build Tools 36.0.0; NDK 27.2.12479018; Java 17.

Source license: GPL-2.0-or-later, https://github.com/DrKLO/Telegram. All further modifications should remain public in compliance with upstream licensing.
