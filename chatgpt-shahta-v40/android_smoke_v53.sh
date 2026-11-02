#!/usr/bin/env bash
set -euo pipefail

mkdir -p screenshots
adb shell wm size 360x760
adb shell wm density 160
adb shell input keyevent KEYCODE_WAKEUP
adb install -r smoke-apks/Shahta-Bez-Dna-v5.3.apk
adb shell am start -W -n com.bezdna.mine/.MainActivity
python3 -m pip install --disable-pip-version-check --quiet Pillow

capture_ready() {
  local target="$1" max_attempts="${2:-55}"
  for attempt in $(seq 1 "$max_attempts"); do
    adb exec-out screencap -p > "$target" || true
    if python3 - "$target" <<'PY'
import sys
from pathlib import Path
from PIL import Image, ImageStat
try:
    path=Path(sys.argv[1])
    im=Image.open(path).convert("RGB")
    assert im.width>=320 and im.height>=640
    mean=sum(ImageStat.Stat(im.crop((20,120,340,620))).mean)/3
    assert path.stat().st_size>12000 and mean>18, (path,mean)
except Exception as exc:
    print("Waiting for rendered UI:",exc)
    sys.exit(1)
PY
    then
      echo "Rendered screen: $target"
      return 0
    fi
    sleep 2
  done
  echo "::error::Game screen remained black or incomplete: $target"
  return 1
}

adb shell pidof com.bezdna.mine
capture_ready screenshots/01-mine.png
# Emulator 360x760 includes status and system navigation; Canvas tabs are at y~680.
adb shell input tap 109 680
sleep 3
capture_ready screenshots/02-shop.png
adb shell input tap 324 680
sleep 3
capture_ready screenshots/03-atlas.png
adb shell pidof com.bezdna.mine
adb logcat -d -s AndroidRuntime:E ActivityManager:E | tail -n 90 || true

python3 - <<'PY'
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
files=sorted(Path("screenshots").glob("*.png"))
assert len(files)==3,files
images=[]
for path in files:
    im=Image.open(path).convert("RGB")
    assert im.width>=320 and im.height>=640
    mean=sum(ImageStat.Stat(im.crop((20,120,340,620))).mean)/3
    assert path.stat().st_size>12000 and mean>18,(path,mean)
    images.append(im)
    print(path,path.stat().st_size,im.size,round(mean,2))
for i in range(2):
    first=images[i].crop((10,120,350,630))
    second=images[i+1].crop((10,120,350,630))
    delta=sum(ImageStat.Stat(ImageChops.difference(first,second)).mean)/3
    assert delta>8,(files[i],files[i+1],delta)
    print("Page transition visual delta:",round(delta,2))
PY

# Visual audit: seed the app's *debug emulator only* SharedPreferences.
# This never modifies a user's phone, APK, import/export schema or release data.
if adb shell run-as com.bezdna.mine pwd >/dev/null 2>&1; then
  mkdir -p screenshots/biomes
  for biome in $(seq 0 23); do
    depth=$((biome*25+1))
    adb shell am force-stop com.bezdna.mine
    adb shell run-as com.bezdna.mine mkdir -p shared_prefs
    printf '<?xml version="1.0" encoding="utf-8" standalone="yes" ?><map><int name="depth" value="%s" /><int name="discovered" value="24" /></map>\n' "$depth" | adb shell run-as com.bezdna.mine sh -c 'cat > shared_prefs/mine_save_v1.xml'
    adb shell am start -W -n com.bezdna.mine/.MainActivity >/dev/null
    sleep 1
    capture_ready "screenshots/biomes/$(printf '%02d' "$biome").png" 16
  done
  python3 - <<'PY'
from pathlib import Path
from PIL import Image, ImageStat
paths=sorted(Path("screenshots/biomes").glob("*.png"))
assert len(paths)==24,len(paths)
means=[]
for path in paths:
    im=Image.open(path).convert("RGB")
    mean=sum(ImageStat.Stat(im.crop((20,120,340,620))).mean)/3
    assert mean>18,(path,mean)
    means.append(round(mean,1))
print("24 biome screenshots validated; average scene luminance:",means)
PY
else
  echo "::warning::Android run-as unavailable; 24-biome debug visual audit skipped"
fi
