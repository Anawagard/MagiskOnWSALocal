"""Source-only audit of the v7.0 raster identity; no asset generation or APK build.

Run after generate_art_v70.py has populated the Android assets directory.
This script reads files only and fails closed on missing or corrupt sprites.
"""
from pathlib import Path
from hashlib import sha256
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "chatgpt-shahta-v33/project/app/src/main/assets/shahta_v70"

def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def audit(directory=ASSETS):
    require(directory.is_dir(), f"Raster assets missing: {directory}")
    required = {f"biome_{i:02d}.jpg" for i in range(24)}
    required |= {f"ore_{i:02d}.png" for i in range(24)}
    required |= {f"menu_{i}.jpg" for i in range(1, 5)}
    required |= {"panel.png", "button.png", "button_off.png",
                 "header.png", "nav.png", "fractures.png", "miner.png"}
    present = {p.name for p in directory.iterdir() if p.is_file()}
    missing = sorted(required - present)
    require(not missing, f"Missing raster assets ({len(missing)}): {missing}")
    fingerprints = {}
    for name in sorted(required):
        file = directory / name
        require(file.stat().st_size > 1024, f"Suspiciously small sprite: {name}")
        with Image.open(file) as im:
            im.verify()
        with Image.open(file) as im:
            im.load()  # Force full pixel decoding, not only header verification.
            width, height = im.size
            expected_format = "JPEG" if name.endswith(".jpg") else "PNG"
            require(im.format == expected_format,
                    f"Unexpected encoding for {name}: {im.format}, expected {expected_format}")
            # Fingerprint decoded pixels, not compressed bytes: catches copied art
            # even when the files have different metadata or compression settings.
            digest = sha256(im.convert("RGBA").tobytes()).hexdigest()
            require(digest not in fingerprints,
                    f"Duplicate raster content: {name} and {fingerprints.get(digest)}")
            fingerprints[digest] = name
            require(width >= 32 and height >= 32, f"Too small: {name} {im.size}")
            # Enforce authored dimensions to catch accidental asset rescaling.
            if name.startswith("biome_") or name.startswith("menu_"):
                require(im.size == (360, 570),
                        f"Incorrect cave background dimensions: {name} {im.size}")
                require(im.mode == "RGB", f"Background must be RGB: {name} ({im.mode})")
            elif name.startswith("ore_"):
                require(im.size == (300, 300),
                        f"Incorrect ore dimensions: {name} {im.size}")
            if name.startswith("ore_") or name in ("miner.png", "fractures.png"):
                require(im.mode in ("RGBA", "LA", "P"), f"Missing alpha-capable sprite: {name}")
                alpha = im.convert("RGBA").getchannel("A")
                lo, hi = alpha.getextrema()
                require(lo < 255 and hi > 0, f"Sprite lacks transparent pixels: {name}")
                if name.startswith("ore_"):
                    require(alpha.getpixel((0, 0)) == 0,
                            f"Ore has opaque top-left corner: {name}")
                    require(alpha.getpixel((width // 2, height // 2)) >= 240,
                            f"Ore center unexpectedly transparent: {name}")
    print(f"PASS: {len(required)} raster assets decoded; 24 biomes, 24 ores, menu and UI art.")

if __name__ == "__main__":
    audit()
