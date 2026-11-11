"""Generate contact sheets for human review without Android, Gradle or Actions.

Run: python3 chatgpt-shahta-v40/preview_raster_source_only_v118.py --output /tmp/shahta-preview
Only pure rendering functions are extracted from generate_art_v70.py. No
Android baseline is restored and no files are written into the repository.
"""
import argparse
import ast
from pathlib import Path
import hashlib
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


def sheet(paths, columns, cell, label, destination, captions=None):
    """Compose an indexed atlas; optional captions identify actual UI assets."""
    if columns < 1 or cell[0] <= 16 or cell[1] <= 35:
        raise ValueError("Invalid contact sheet grid or cell size")
    if captions is not None and len(captions) != len(paths):
        raise ValueError("Captions must match image count")
    from PIL import Image, ImageDraw
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
        # Fit captions within their own tile: a long localized name must not
        # overwrite the adjacent tile's label or spill outside the atlas.
        available = cell[0] - 16
        while caption and draw.textbbox((0, 0), caption)[2] > available:
            caption = caption[:-1]
        draw.text(((i % columns) * cell[0] + 8, (i // columns) * cell[1] + 6),
                  caption, fill=(93, 224, 210))
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True,
                        help="Existing or new directory outside the repository")
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
    print(f"Created 4 contact sheets in {output}")


if __name__ == "__main__":
    main()
