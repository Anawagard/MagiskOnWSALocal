"""Generate contact sheets for human review without Android, Gradle or Actions.

Run: python3 chatgpt-shahta-v40/preview_raster_source_only_v118.py --output /tmp/shahta-preview
Only pure rendering functions are extracted from generate_art_v70.py. No
Android baseline is restored and no files are written into the repository.
"""
import argparse
import ast
from pathlib import Path
import hashlib
import shutil
from tempfile import TemporaryDirectory

SOURCE = Path(__file__).with_name("generate_art_v70.py")
NAMES = {"field", "image_array", "cave", "ore", "panel_art"}
PALETTES = {"SCENES", "ORES"}


def load_renderers():
    import math
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter, ImageChops
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    nodes = []
    found = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in NAMES:
            nodes.append(node)
            found.add(node.name)
        elif isinstance(node, ast.Assign):
            names = {t.id for t in node.targets if isinstance(t, ast.Name)}
            if names & PALETTES:
                nodes.append(node)
                found |= names & PALETTES
    assert found == NAMES | PALETTES, f"Missing generator definitions: {(NAMES | PALETTES) - found}"
    env = dict(math=math, np=np, Image=Image, ImageDraw=ImageDraw,
               ImageFilter=ImageFilter, ImageChops=ImageChops,
               R=Image.Resampling.BICUBIC)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), env)
    assert len(env["SCENES"]) == len(env["ORES"]) == 24
    return env


def _font_supports(font, character):
    """Whether Pillow can measure a character using the selected font."""
    try:
        font.getbbox(character)
        return True
    except UnicodeEncodeError:
        return False


def sheet(paths, columns, cell, label, destination, captions=None):
    """Compose an indexed atlas; optional captions identify actual UI assets."""
    if columns < 1 or cell[0] <= 16 or cell[1] <= 35:
        raise ValueError("Invalid contact sheet grid or cell size")
    if captions is not None and len(captions) != len(paths):
        raise ValueError("Captions must match image count")
    from PIL import Image, ImageDraw, ImageFont
    # Pillow's bitmap default font can reject Cyrillic and other UI labels.
    # DejaVu Sans is available in standard Pillow/Linux environments.
    try:
        caption_font = ImageFont.truetype("DejaVuSans.ttf", 12)
    except OSError:
        caption_font = ImageFont.load_default()
    if not paths:
        raise ValueError("Contact sheet requires at least one image")
    rows = (len(paths) + columns - 1) // columns
    out = Image.new("RGB", (columns * cell[0], rows * cell[1]), (13, 20, 31))
    draw = ImageDraw.Draw(out)
    for i, path in enumerate(paths):
        with Image.open(path) as original:
            thumb = original.convert("RGBA")
            thumb.thumbnail((cell[0] - 16, cell[1] - 35), Image.Resampling.LANCZOS)
            x = (i % columns) * cell[0] + (cell[0] - thumb.width) // 2
            y = (i // columns) * cell[1] + 25
            # Checkerboard exposes alpha-edge defects in ore sprite previews.
            if "A" in original.getbands() or "transparency" in original.info:
                for yy in range(y, y + thumb.height, 12):
                    for xx in range(x, x + thumb.width, 12):
                        parity = ((xx - x) // 12 + (yy - y) // 12) % 2
                        draw.rectangle(
                            (xx, yy, min(xx + 11, x + thumb.width - 1),
                             min(yy + 11, y + thumb.height - 1)),
                            fill=(49, 59, 70) if parity else (91, 102, 111)
                        )
            out.paste(thumb, (x, y), thumb)
        caption = str(captions[i] if captions is not None else f"{label} {i + 1:02d}")
        # Imported/localized names may contain line breaks or control chars.
        # Keep every caption on a single line inside its own atlas tile.
        caption = " ".join("".join(ch if ch.isprintable() else " " for ch in caption).split())
        # Pillow's fallback bitmap font may not encode localized glyphs.
        # Replace only unsupported characters, keeping the preview usable
        # instead of failing the entire source-only atlas generation.
        try:
            draw.textbbox((0, 0), caption, font=caption_font)
        except UnicodeEncodeError:
            caption = "".join(
                ch if _font_supports(caption_font, ch) else "?"
                for ch in caption
            )
        # Fit captions within their own tile: a long localized name must not
        # overwrite the adjacent tile's label or spill outside the atlas.
        available = cell[0] - 16
        def fits(value):
            try:
                bounds = draw.textbbox((0, 0), value, font=caption_font)
            except UnicodeEncodeError:
                return False
            return bounds[2] - bounds[0] <= available
        if not fits(caption):
            suffix = "…" if fits("…") else "..."
            # Binary-search the longest fitting prefix. A linear trim makes
            # long imported captions quadratic in text measurement work.
            lo, hi = 0, len(caption)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if fits(caption[:mid] + suffix):
                    lo = mid
                else:
                    hi = mid - 1
            caption = caption[:lo] + suffix if lo else (suffix if fits(suffix) else "")
        # Font ink can have positive or negative bearings. Align the actual
        # painted bounds to the tile inset, not the font drawing origin.
        if caption:
            ink = draw.textbbox((0, 0), caption, font=caption_font)
            caption_x = (i % columns) * cell[0] + 8 - ink[0]
            caption_y = (i // columns) * cell[1] + 6 - ink[1]
            # Render captions into a tile-local buffer. Font overhangs and
            # unusual glyph metrics must never paint adjacent atlas cells.
            tile = Image.new("RGBA", cell, (0, 0, 0, 0))
            tile_draw = ImageDraw.Draw(tile)
            tile_draw.text((caption_x - (i % columns) * cell[0],
                            caption_y - (i // columns) * cell[1]),
                           caption, fill=(93, 224, 210, 255),
                           font=caption_font)
            out.paste(tile, ((i % columns) * cell[0],
                             (i // columns) * cell[1]), tile)
    out.save(destination, optimize=True)


def audit_unique_images(paths, label):
    """Reject exact duplicate raster outputs; same palette is not enough."""
    digests = {}
    for path in paths:
        from PIL import Image
        with Image.open(path) as image:
            image.load()
            fingerprint = hashlib.sha256(
                image.mode.encode("ascii") + str(image.size).encode("ascii")
                + image.tobytes()
            ).hexdigest()
        if fingerprint in digests:
            raise ValueError(
                f"{label} raster duplicate: {digests[fingerprint].name} and {path.name}"
            )
        digests[fingerprint] = path
    return len(digests)


def audit_ore_alpha(paths):
    """Require both visible ore pixels and transparent sprite margins."""
    from PIL import Image
    for path in paths:
        with Image.open(path) as image:
            rgba = image.convert("RGBA")
            alpha = rgba.getchannel("A")
            low, high = alpha.getextrema()
            if low != 0 or high != 255:
                raise ValueError(
                    f"ORE alpha contract failed for {path.name}: extrema {low, high}"
                )
            # A single opaque pixel plus a transparent canvas passes extrema,
            # but produces an invisible ore in the actual mine. Measure coverage
            # with the same alpha threshold used by sprite compositing.
            histogram = alpha.histogram()
            visible = sum(histogram[128:])
            total = rgba.width * rgba.height
            coverage = visible / total
            if not 0.15 <= coverage <= 0.85:
                raise ValueError(
                    f"ORE visible coverage failed for {path.name}: "
                    f"{coverage:.3%} (expected 15%-85%)"
                )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True,
                        help="Existing or new directory outside the repository")
    parser.add_argument("--keep-assets", action="store_true",
                        help="Also export individual rendered sprites for pixel-level review")
    args = parser.parse_args()
    output = args.output.resolve()
    repo = SOURCE.resolve().parent.parent
    if output == repo or repo in output.parents:
        parser.error("--output must be outside the repository")
    env = load_renderers()
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as tmp:
        temp = Path(tmp)
        biomes, ores = [], []
        for i in range(24):
            biome = temp / f"biome_{i:02d}.jpg"
            mineral = temp / f"ore_{i:02d}.png"
            env["cave"](i, env["SCENES"][i], biome)
            env["ore"](i, env["ORES"][i], mineral)
            biomes.append(biome)
            ores.append(mineral)
        audit_unique_images(biomes, "BIOME")
        audit_unique_images(ores, "ORE")
        audit_ore_alpha(ores)
        sheet(biomes, 6, (180, 310), "BIOME", output / "biomes_contact.png")
        sheet(ores, 6, (180, 190), "ORE", output / "ores_contact.png")
        # Menu backdrops are generated by the same cave renderer as release art.
        # Audit all four separately: they are not included in the 24 biome tiles.
        menu_paths = []
        for j, base in enumerate(((59, 118, 137), (132, 74, 51),
                                  (73, 108, 133), (101, 93, 143)), start=1):
            target = temp / f"menu_{j}.jpg"
            env["cave"](30 + j, base, target)
            menu_paths.append(target)
        audit_unique_images(menu_paths, "MENU")
        sheet(menu_paths, 4, (180, 310), "MENU", output / "menus_contact.png")
        skins = [
            ("panel", (23, 32, 47), (85, 125, 148), (400, 96), False),
            ("button", (21, 103, 109), (92, 227, 207), (160, 64), True),
            ("button_off", (32, 44, 58), (91, 112, 131), (160, 64), False),
            ("header", (17, 27, 42), (85, 132, 156), (360, 88), False),
            ("nav", (17, 28, 42), (90, 150, 164), (360, 50), False),
        ]
        skin_paths = []
        for name, base, border, size, bright in skins:
            target = temp / (name + ".png")
            env["panel_art"](target, base, border, size=size, bright=bright)
            skin_paths.append(target)
        sheet(skin_paths, 2, (220, 135), "SKIN", output / "skins_contact.png",
              captions=[name.upper() for name, *_ in skins])
        if args.keep_assets:
            assets = output / "individual_assets"
            assets.mkdir(parents=True, exist_ok=True)
            for source in (*biomes, *ores, *menu_paths, *skin_paths):
                shutil.copy2(source, assets / source.name)
    print(f"Created 4 contact sheets in {output}" +
          (" and 57 individual assets" if args.keep_assets else ""))


if __name__ == "__main__":
    main()
