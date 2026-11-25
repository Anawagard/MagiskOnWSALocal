"""Build a complete 24x24 ore-over-biome visual review atlas (source-only).

Unlike the risk contact sheet, this includes *every* pairing, even those
passing numeric contrast thresholds. It never changes Android or game assets.

python preview_all_ore_biome_pairs_source_only.py --assets /path/to/shahta_v70 --output /tmp/ore-atlas.png
"""
import argparse
import os
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from audit_ore_biome_composites_source_only import (
    COUNT, BACKGROUND_SIZE, ORE_SIZE, ore_backdrop, read_ore, read_rgb,
    validate_diagnostic_destination,
)


def render_atlas(assets, output, tile=96):
    assets = Path(assets)
    destination = validate_diagnostic_destination(assets, output)
    if type(tile) is not int or not 48 <= tile <= 256:
        raise ValueError("tile must be an integer in [48, 256]")
    # Validate all input assets before publishing any output.
    backgrounds = [
        ore_backdrop(read_rgb(assets / f"biome_{i:02d}.jpg",
                              BACKGROUND_SIZE, "JPEG"), sample_size=tile)
        for i in range(COUNT)
    ]
    foregrounds = [
        read_ore(assets / f"ore_{i:02d}.png", sample_size=tile)
        for i in range(COUNT)
    ]
    gutter, header = 3, 28
    step = tile + gutter
    sheet = Image.new("RGB", (header + COUNT * step + gutter,
                              header + COUNT * step + gutter), (20, 26, 34))
    draw = ImageDraw.Draw(sheet)
    for i in range(COUNT):
        draw.text((header + i * step + 4, 7), f"{i+1:02d}", fill=(138, 233, 219))
        draw.text((4, header + i * step + 5), f"{i+1:02d}", fill=(218, 232, 231))
    for biome, background in enumerate(backgrounds):
        backdrop = background.convert("RGBA")
        for ore, foreground in enumerate(foregrounds):
            combined = Image.alpha_composite(backdrop, foreground).convert("RGB")
            sheet.paste(combined, (header + ore * step, header + biome * step))
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".shahta-all-pairs-", suffix=".png",
            dir=destination.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
        sheet.save(temporary, format="PNG")
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tile", type=int, default=96)
    args = parser.parse_args()
    print(render_atlas(args.assets, args.output, args.tile))


if __name__ == "__main__":
    main()
