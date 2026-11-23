"""Fail-closed source-only audit of the generated v7 raster art pack.

Runs after generate_art_v70.py and before any Android compilation.
Never starts Gradle, an emulator, or GitHub Actions.
"""
from pathlib import Path
from PIL import Image, ImageStat
import hashlib

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "chatgpt-shahta-v33/project/app/src/main/assets/shahta_v70"

def audit():
    assert ASSETS.is_dir(), f"Missing generated art pack: {ASSETS}"
    for kind, extension in (("ore", "png"), ("biome", "jpg")):
        names = [ASSETS / f"{kind}_{i:02d}.{extension}" for i in range(24)]
        actual = sorted(ASSETS.glob(f"{kind}_*.{extension}"))
        assert sorted(names) == actual, f"{kind}: expected exactly 24 sequential assets"
        fingerprints = set()
        for path in names:
            assert path.stat().st_size > 12000, f"Too small: {path.name}"
            with Image.open(path) as image:
                image.load()  # detect truncated/corrupt files
                assert image.width >= 96 and image.height >= 96, path.name
                assert image.mode in ("RGB", "RGBA"), (path.name, image.mode)
                rgb = image.convert("RGB")
                extrema = ImageStat.Stat(rgb).stddev
                assert max(extrema) > 8, f"Nearly flat texture: {path.name}"
                digest = hashlib.sha256(rgb.tobytes()).digest()
                assert digest not in fingerprints, f"Duplicate decoded pixels: {path.name}"
                fingerprints.add(digest)
                if kind == "ore":
                    assert image.mode == "RGBA", f"Ore lost transparency: {path.name}"
                    alpha = image.getchannel("A")
                    low, high = alpha.getextrema()
                    assert low == 0 and high == 255, f"Ore alpha mask invalid: {path.name}"
        assert len(fingerprints) == 24
        print(f"PASS: {kind}: 24 decoded, non-flat, unique raster assets")

if __name__ == "__main__":
    audit()
