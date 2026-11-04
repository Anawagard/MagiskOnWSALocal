"""Source-only audit of the v7.0 raster identity; no asset generation or APK build.

Run after generate_art_v70.py has populated the Android assets directory.
This script reads files only and fails closed on missing or corrupt sprites.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "chatgpt-shahta-v33/project/app/src/main/assets/shahta_v70"

def audit(directory=ASSETS):
    assert directory.is_dir(), f"Raster assets missing: {directory}"
    required = {f"biome_{i:02d}.jpg" for i in range(24)}
    required |= {f"ore_{i:02d}.png" for i in range(24)}
    required |= {f"menu_{i}.jpg" for i in range(1, 5)}
    required |= {"panel.png", "button.png", "button_off.png",
                 "header.png", "nav.png", "fractures.png", "miner.png"}
    present = {p.name for p in directory.iterdir() if p.is_file()}
    missing = sorted(required - present)
    assert not missing, f"Missing raster assets ({len(missing)}): {missing}"
    for name in sorted(required):
        file = directory / name
        assert file.stat().st_size > 1024, f"Suspiciously small sprite: {name}"
        with Image.open(file) as im:
            im.verify()
        with Image.open(file) as im:
            width, height = im.size
            assert width >= 32 and height >= 32, f"Too small: {name} {im.size}"
            if name.startswith("ore_") or name in ("miner.png", "fractures.png"):
                assert im.mode in ("RGBA", "LA", "P"), f"Missing alpha-capable sprite: {name}"
                assert "A" in im.convert("RGBA").getbands()
    print(f"PASS: {len(required)} raster assets decoded; 24 biomes, 24 ores, five-screen art.")

if __name__ == "__main__":
    audit()
