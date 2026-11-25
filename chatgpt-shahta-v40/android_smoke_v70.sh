#!/usr/bin/env bash
set -euo pipefail

package="${SHAHTA_SMOKE_PACKAGE:-com.bezdna.mine}"
case "$package" in
  com.bezdna.mine|com.bezdna.mine.redesign) ;;
  *) echo "Unexpected Shahta package: $package" >&2; exit 1 ;;
esac
activity="$package/com.bezdna.mine.MainActivity"

mkdir -p screenshots
adb shell wm size 360x760
adb shell wm density 160
adb shell input keyevent KEYCODE_WAKEUP
apk="${SHAHTA_SMOKE_APK:-}"
if [ -z "$apk" ]; then
  for candidate in smoke-apks/Shahta-Bez-Dna-v*.apk; do
    if [[ "$candidate" != *Parallel.apk ]]; then apk="$candidate"; break; fi
  done
fi
test -f "$apk"
adb install --no-streaming -r "$apk"
adb shell am start -W -n "$activity"
python3 -m pip install --disable-pip-version-check --quiet Pillow

capture_ready() {
  local target="$1" max_attempts="${2:-55}"
  local focus
  for attempt in $(seq 1 "$max_attempts"); do
    # Screenshot brightness alone also accepts the launcher and Android
    # error dialogs. Wait until the game actually owns input focus.
    focus="$(adb shell dumpsys window windows | sed -n '/mCurrentFocus=/p')"
    if [[ "$focus" != *" $activity}"* && "$focus" != *" $package/.MainActivity}"* ]]; then
      sleep 2
      continue
    fi
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

adb shell pidof "$package"
capture_ready screenshots/01-mine.png
# Exercise actual mining, fracture surfaces and hit/debris rendering.
adb shell input tap 180 329
adb shell input tap 180 329
adb shell input tap 180 329
sleep 0.2
capture_ready screenshots/01b-damage.png
# Emulator 360x760 includes status and system navigation; v7.0 top navigation tabs are at y~135.
adb shell input tap 109 135
sleep 3
capture_ready screenshots/02-shop.png
adb shell input tap 324 135
sleep 3
capture_ready screenshots/03-atlas.png
adb shell input tap 252 135
sleep 2
capture_ready screenshots/03a-guild.png
adb shell pidof "$package"
adb logcat -d -s AndroidRuntime:E ActivityManager:E | tail -n 90 || true

python3 - <<'PY'
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
files=sorted(Path("screenshots").glob("*.png"))
assert len(files)==5,files
images=[]
for path in files:
    im=Image.open(path).convert("RGB")
    assert im.width>=320 and im.height>=640
    mean=sum(ImageStat.Stat(im.crop((20,120,340,620))).mean)/3
    assert path.stat().st_size>12000 and mean>18,(path,mean)
    images.append(im)
    print(path,path.stat().st_size,im.size,round(mean,2))
damage_delta=sum(ImageStat.Stat(ImageChops.difference(
    images[0].crop((70,220,290,465)),images[1].crop((70,220,290,465)))).mean)/3
assert damage_delta>1.2,("Textured ore fracture did not change",damage_delta)
print("Mining damage visual delta:",round(damage_delta,2))
for i,j in ((0,2),(2,3),(3,4),(2,4)):
    first=images[i].crop((10,120,350,630))
    second=images[j].crop((10,120,350,630))
    delta=sum(ImageStat.Stat(ImageChops.difference(first,second)).mean)/3
    assert delta>8,(files[i],files[j],delta)
    print("Page transition visual delta:",round(delta,2))
PY

# v6.3 visual regression coverage: shop technology page and four forge tabs.
# Only screenshots are taken; no upgrade buttons or player data are modified.
adb shell input tap 109 135
sleep 1
# The v7.4 shop tabs live at page y=130..158, translated down by 60,
# plus the emulator status bar (~24px): physical tap y=225.
# First verify that the v7.3 settings sheet can open and close.
adb shell input tap 295 212
sleep 1
capture_ready screenshots/03b-settings.png
adb shell input tap 180 637
sleep 1
adb shell input tap 180 225
sleep 1
capture_ready screenshots/04-tech-shop.png
python3 - <<'PY'
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
shop=Image.open('screenshots/02-shop.png').convert('RGB')
settings=Image.open('screenshots/03b-settings.png').convert('RGB')
tech=Image.open('screenshots/04-tech-shop.png').convert('RGB')
for name,other in [('settings',settings),('technology tab',tech)]:
    a=shop.crop((18,230,342,635))
    b=other.crop((18,230,342,635))
    delta=sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3
    assert delta>3,(name,delta)
    print('Modernist UI transition:',name,round(delta,2))
PY
adb shell input tap 180 135
sleep 1
capture_ready screenshots/05-forge-relics.png
for item in "136:06-forge-talents" "222:07-forge-runes" "307:08-forge-mastery"; do
  x="${item%%:*}"
  name="${item#*:}"
  adb shell input tap "$x" 232
  sleep 1
  capture_ready "screenshots/${name}.png"
done
python3 - <<'PY'
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
files=[Path('screenshots')/f for f in (
  '04-tech-shop.png','05-forge-relics.png','06-forge-talents.png',
  '07-forge-runes.png','08-forge-mastery.png')]
for path in files:
    assert path.is_file(),path
    assert path.stat().st_size>12000,path
for a,b in zip(files,files[1:]):
    ia=Image.open(a).convert('RGB').crop((15,180,345,635))
    ib=Image.open(b).convert('RGB').crop((15,180,345,635))
    delta=sum(ImageStat.Stat(ImageChops.difference(ia,ib)).mean)/3
    assert delta>3,(a,b,delta)
    print('Upgrade UI screenshot difference:',a.name,b.name,round(delta,2))
PY

# Visual audit: seed the app's *debug emulator only* SharedPreferences.
# This never modifies a user's phone, APK, import/export schema or release data.
if adb shell run-as "$package" pwd >/dev/null 2>&1; then
  mkdir -p screenshots/biomes
  for biome in $(seq 0 23); do
    depth=$((biome*25+1))
    adb shell am force-stop "$package"
    adb shell run-as "$package" mkdir -p shared_prefs
    printf '<?xml version="1.0" encoding="utf-8" standalone="yes" ?><map><int name="depth" value="%s" /><int name="discovered" value="24" /></map>\n' "$depth" | adb shell "run-as $package sh -c 'cat > shared_prefs/mine_save_v1.xml'"
    adb shell am start -W -n "$activity" >/dev/null
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
  echo "::error::Android run-as unavailable; the 24-biome visual audit requires the debug APK"
  exit 1
fi
