# OnePlus 15 / ColorOS 17 test matrix
- Verify signature, package dev.fluidgram.oneplus15.web, login and 2FA.
- Record front-camera 10, 30, 60s circles; switch front/back 1x and 3x; repeat 30 times.
- Check green frames, audio/video sync, dropped frames, Camera2 on/off, 30fps.
- Only enable 60fps if both supported camera streams and encoder confirm support.
- Benchmark animation before/after; respect Android reduced-motion/animation-scale.
- Validate notifications, calls, camera/microphone permission indicator, battery and thermals.
- Check dark/light theme and status bar/cutouts on ColorOS 17.
