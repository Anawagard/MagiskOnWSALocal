"""Generate contact sheets for human review of all 24 biomes and 24 ores.

Source-only: never invokes Gradle, Android, or GitHub Actions.
Usage: python preview_raster_contact_sheets.py ASSET_DIRECTORY OUTPUT_DIRECTORY
The output directory must exist and must differ from the asset directory.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import argparse
import hashlib


def make_sheet(assets: Path, destination: Path, kind: str) -> Path:
    is_biome = kind == "biome"
    tile = (180, 285) if is_biome else (180, 180)
    margin, caption, columns = 12, 26, 6
    width = columns * (tile[0] + margin) + margin
    height = 4 * (tile[1] + caption + margin) + margin
    sheet = Image.new("RGB", (width, height), (17, 25, 37))
    draw = ImageDraw.Draw(sheet)
    for index in range(24):
        filename = f"{kind}_{index:02d}." + ("jpg" if is_biome else "png")
        path = assets / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing {path}")
        with Image.open(path) as original:
            original.load()
            expected = (360, 570) if is_biome else (300, 300)
            if original.size != expected:
                raise ValueError(f"{filename}: expected {expected}, got {original.size}")
            rgba = original.convert("RGBA")
            # Compose alpha onto the game's graphite rather than a white matte.
            backdrop = Image.new("RGBA", rgba.size, (23, 32, 47, 255))
            visible = Image.alpha_composite(backdrop, rgba).convert("RGB")
            thumbnail = ImageOps.fit(visible, tile, method=Image.Resampling.LANCZOS)
        x = margin + (index % columns) * (tile[0] + margin)
        y = margin + (index // columns) * (tile[1] + caption + margin)
        sheet.paste(thumbnail, (x, y))
        draw.text((x + 4, y + tile[1] + 5), f"{kind.upper()} {index:02d}",
                  fill=(109, 229, 216), font=ImageFont.load_default())
    target = destination / f"{kind}_contact_sheet.png"
    sheet.save(target, optimize=True)
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("assets", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    assets, output = args.assets.resolve(), args.output.resolve()
    if not assets.is_dir() or not output.is_dir() or assets == output:
        parser.error("Existing, distinct assets and output directories are required")
    # A preview destination nested in the asset directory can accidentally be
    # packaged into Android resources by a later copy step. Keep it separate.
    if assets in output.parents or output in assets.parents:
        parser.error("Preview output and assets must not contain one another")
    # Validate the decoded art, not only the container headers. In particular,
    # an opaque ore PNG can silently render as a square over the mine background.
    # Exact decoded-pixel duplicates indicate a missing palette/biome variant.
    # These checks are deliberately source-only and never invoke Android.
    fingerprints = {}
    # Validate all 48 images before writing either sheet, avoiding partial results.
    for kind, ext, size in (("biome", "jpg", (360, 570)),
                            ("ore", "png", (300, 300))):
        for i in range(24):
            path = assets / f"{kind}_{i:02d}.{ext}"
            if not path.is_file():
                raise FileNotFoundError(f"Missing required {kind} raster: {path}")
            with Image.open(path) as im:
                im.verify()
            with Image.open(path) as im:
                if im.size != size:
                    raise ValueError(f"{path.name}: expected {size}, got {im.size}")
                if kind == "biome" and im.mode not in ("RGB", "L"):
                    raise ValueError(f"{path.name}: biome JPEG must be opaque RGB or grayscale")
                if kind == "ore":
                    if im.mode not in ("RGBA", "LA", "P") or (
                        im.mode == "P" and "transparency" not in im.info
                    ):
                        raise ValueError(f"{path.name}: ore requires transparency")
                    alpha = im.convert("RGBA").getchannel("A")
                    lo, hi = alpha.getextrema()
                    if lo != 0 or hi != 255:
                        raise ValueError(
                            f"{path.name}: ore must contain fully transparent "
                            "background and fully opaque mineral pixels"
                        )
                # Hash decoded RGBA pixels to catch identical variants even if
                # their PNG/JPEG metadata or compression differs.
                digest = hashlib.sha256(im.convert("RGBA").tobytes()).hexdigest()
                previous = fingerprints.get((kind, digest))
                if previous is not None:
                    raise ValueError(f"{path.name}: identical pixels to {previous}")
                fingerprints[(kind, digest)] = path.name
    for kind in ("biome", "ore"):
        print(make_sheet(assets, output, kind))


if __name__ == "__main__":
    main()
