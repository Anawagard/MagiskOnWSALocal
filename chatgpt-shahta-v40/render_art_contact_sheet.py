"""Create reviewable contact sheets from existing v7 raster art (no APK build).

Usage: python render_art_contact_sheet.py --assets PATH --output PATH
Fails on missing/undecodable images. Never changes the source assets.
"""
import argparse
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw, ImageOps

BIOMES = [f"biome_{i:02d}.jpg" for i in range(24)]
ORES = [f"ore_{i:02d}.png" for i in range(24)]
MENUS = [f"menu_{i}.jpg" for i in range(1, 5)]
UI = ["panel.png", "button.png", "button_off.png", "header.png", "nav.png", "fractures.png", "miner.png"]
GROUPS = (("biomes", BIOMES, 6), ("ores", ORES, 6), ("interface", MENUS + UI, 4))
GRAPHITE = (18, 24, 34)
CARD = (32, 43, 55)
CYAN = (75, 223, 218)


def generate(assets: Path, output: Path):
    # Validate all assets before producing any review sheet.
    for group, names, _ in GROUPS:
        for name in names:
            path = assets / name
            if not path.is_file():
                raise FileNotFoundError(f"Missing {group} raster: {path}")
            with Image.open(path) as source:
                source.verify()
            with Image.open(path) as source:
                source.load()
                if source.width < 2 or source.height < 2:
                    raise ValueError(f"Invalid raster dimensions: {path}")
    output.mkdir(parents=True, exist_ok=True)
    # Render all sheets in a staging directory first. An exception while
    # drawing the last group must never leave a partially refreshed review set.
    produced = []
    with tempfile.TemporaryDirectory(prefix="shahta-sheets-", dir=output) as staging:
        staged = []
        for group, names, columns in GROUPS:
            cell_w, cell_h, margin, gap, title_h = 188, 226, 24, 14, 58
            rows = (len(names) + columns - 1) // columns
            width = margin * 2 + columns * cell_w + (columns - 1) * gap
            height = title_h + margin + rows * cell_h + (rows - 1) * gap + margin
            sheet = Image.new("RGB", (width, height), GRAPHITE)
            draw = ImageDraw.Draw(sheet)
            draw.text((margin, 18), f"SHAHTA / {group.upper()} / {len(names)}", fill=CYAN)
            for index, name in enumerate(names):
                path = assets / name
                if not path.is_file():
                    raise FileNotFoundError(f"Missing raster: {path}")
                with Image.open(path) as source:
                    source.load()
                    rgba = source.convert("RGBA")
                    preview = ImageOps.contain(rgba, (cell_w - 20, cell_h - 54), Image.Resampling.LANCZOS)
                x = margin + (index % columns) * (cell_w + gap)
                y = title_h + (index // columns) * (cell_h + gap)
                draw.rounded_rectangle((x, y, x + cell_w - 1, y + cell_h - 1), radius=12, fill=CARD)
                px = x + (cell_w - preview.width) // 2
                py = y + 8 + (cell_h - 54 - preview.height) // 2
                sheet.paste(preview, (px, py), preview)
                draw.text((x + 12, y + cell_h - 30), name, fill=(235, 243, 246))
            destination = Path(staging) / f"shahta_{group}_contact_sheet.png"
            sheet.save(destination, optimize=True)
            staged.append(destination)
            # Only publish after every sheet has been rendered successfully.
        for temporary in staged:
            final = output / temporary.name
            temporary.replace(final)
            produced.append(final)
    return produced


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for path in generate(args.assets, args.output):
        print(path)


if __name__ == "__main__":
    main()
