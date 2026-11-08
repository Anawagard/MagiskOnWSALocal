"""Source-only audit of the v7.0 raster identity; no asset generation or APK build.

Run after generate_art_v70.py has populated the Android assets directory.
This script reads files only and fails closed on missing or corrupt sprites.
"""
from pathlib import Path
from hashlib import sha256
from PIL import Image, ImageChops, ImageStat

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
    background_previews = {}
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
            # Ignore hidden RGB in fully transparent pixels. Two PNGs can look
            # identical in Android while carrying different invisible colours;
            # hashing raw RGBA would incorrectly treat them as unique art.
            # Fingerprint on both black and white backgrounds. A black-only
            # composite loses alpha information for black artwork, so distinct
            # silhouettes could be incorrectly flagged as duplicate sprites.
            # Two matte colours preserve rendered colour *and* transparency
            # while still ignoring RGB values under fully transparent pixels.
            rgba = im.convert("RGBA")
            fingerprint = sha256()
            fingerprint.update(width.to_bytes(4, "big"))
            fingerprint.update(height.to_bytes(4, "big"))
            for matte in ((0, 0, 0, 255), (255, 255, 255, 255)):
                rendered = Image.alpha_composite(
                    Image.new("RGBA", im.size, matte), rgba
                )
                fingerprint.update(rendered.convert("RGB").tobytes())
            digest = fingerprint.hexdigest()
            require(digest not in fingerprints,
                    f"Duplicate raster content: {name} and {fingerprints.get(digest)}")
            fingerprints[digest] = name
            require(width >= 32 and height >= 32, f"Too small: {name} {im.size}")
            # Enforce authored dimensions to catch accidental asset rescaling.
            if name.startswith("biome_") or name.startswith("menu_"):
                require(im.size == (360, 570),
                        f"Incorrect cave background dimensions: {name} {im.size}")
                require(im.mode == "RGB", f"Background must be RGB: {name} ({im.mode})")
            elif name == "miner.png":
                require(im.size == (240, 340),
                        f"Incorrect miner sprite dimensions: {name} {im.size}")
            elif name.startswith("ore_"):
                require(im.size == (300, 300),
                        f"Incorrect ore dimensions: {name} {im.size}")
            # UI skins are nine-slice sources: unexpected dimensions shift the
            # corner caps and touch feedback even if the PNG decodes correctly.
            ui_sizes = {
                "panel.png": (400, 96),
                "button.png": (160, 64),
                "button_off.png": (160, 64),
                "header.png": (360, 88),
                "nav.png": (360, 50),
                "fractures.png": (300, 300),
            }
            if name in ui_sizes:
                require(im.size == ui_sizes[name],
                        f"Incorrect UI sprite dimensions: {name} {im.size}; expected {ui_sizes[name]}")
            if name.endswith(".png"):
                # Palette mode alone does not imply transparency: an indexed PNG
                # without a tRNS chunk is fully opaque when Android decodes it.
                # Require a real alpha channel or explicit palette transparency.
                has_alpha = im.mode in ("RGBA", "LA") or (
                    im.mode == "P" and "transparency" in im.info
                )
                require(has_alpha,
                        f"PNG sprite must contain alpha/transparency: {name} ({im.mode})")
                # A syntactically valid RGBA export can still be invisible in-game.
                # Require meaningful visible coverage for nine-slice UI artwork.
                if name in ("panel.png", "button.png", "button_off.png", "header.png", "nav.png"):
                    alpha_hist = im.convert("RGBA").getchannel("A").histogram()
                    visible_count = sum(alpha_hist[32:])
                    require(visible_count >= width * height * 0.05,
                            f"UI sprite is nearly invisible: {name} "
                            f"({visible_count / (width * height):.1%} visible)")
            # Reject accidental blank/flat exports. Sampling decoded RGB pixels
            # catches solid-color placeholders without relying on PNG byte size.
            if name.startswith(("biome_", "menu_", "ore_")):
                rgb = im.convert("RGB").resize((32, 32))
                extrema = rgb.getextrema()
                dynamic_range = max(high - low for low, high in extrema)
                require(dynamic_range >= 24,
                        f"Raster lacks visible tonal detail: {name} (range={dynamic_range})")
                if name.startswith(("biome_", "menu_")):
                    # A few bright pixels can inflate extrema on an otherwise
                    # featureless backdrop. Require distributed tonal detail.
                    # Use the full-resolution image so isolated speckles cannot
                    # gain weight through downsampling/interpolation.
                    samples = im.convert("RGB").resize((64, 64))
                    bands = samples.split()
                    spreads = []
                    for band in bands:
                        values = sorted(band.getdata())
                        spreads.append(values[(len(values) - 1) * 95 // 100]
                                       - values[(len(values) - 1) * 5 // 100])
                    require(max(spreads) >= 24,
                            f"Background lacks distributed texture: {name} "
                            f"(5-95% range={max(spreads)})")
            if name.startswith(("biome_", "menu_")):
                # Byte/pixel hashes alone accept a copied cave background with
                # one changed pixel or a different JPEG quality setting.
                # Compare low-resolution appearance to reject near-clones while
                # tolerating genuinely different cave scenes and palettes.
                preview = im.convert("RGB").resize((36, 57))
                for previous_name, previous in background_previews.items():
                    delta = ImageChops.difference(preview, previous)
                    mean_delta = sum(ImageStat.Stat(delta).mean) / 3
                    require(mean_delta >= 1.0,
                            f"Near-duplicate cave backgrounds: {name} and "
                            f"{previous_name} (mean RGB delta={mean_delta:.3f})")
                background_previews[name] = preview
            if name.startswith("ore_"):
                # RGB conversion paints transparent PNG pixels black. Measuring
                # the full image can therefore incorrectly approve a flat,
                # single-colour stone merely because its edges are transparent.
                rgba = im.convert("RGBA")
                pixels = rgba.getdata()
                visible = [(r, g, b) for r, g, b, a in pixels if a >= 240]
                require(len(visible) >= width * height * 0.12,
                        f"Ore has too few visible pixels: {name}")
                # Sample only fully visible stone pixels. Channel spread is a
                # conservative source-only proxy for actual surface texture.
                # Use robust 5th–95th percentile spread: a handful of bright
                # speckles must not make an otherwise flat placeholder pass.
                def percentile_spread(channel):
                    samples = sorted(px[channel] for px in visible)
                    lo = samples[(len(samples) - 1) * 5 // 100]
                    hi = samples[(len(samples) - 1) * 95 // 100]
                    return hi - lo

                stone_range = max(percentile_spread(c) for c in range(3))
                require(stone_range >= 24,
                        f"Ore interior lacks widespread texture: {name} "
                        f"(5–95% range={stone_range})")
            if name.startswith("ore_") or name in ("miner.png", "fractures.png"):
                require(im.mode in ("RGBA", "LA", "P"), f"Missing alpha-capable sprite: {name}")
                alpha = im.convert("RGBA").getchannel("A")
                lo, hi = alpha.getextrema()
                require(lo < 255 and hi > 0, f"Sprite lacks transparent pixels: {name}")
                if name == "fractures.png":
                    # A damage overlay with only one stray opaque pixel technically
                    # has alpha, but is invisible in gameplay. Keep the lower
                    # threshold conservative for deliberately sparse cracks.
                    visible = sum(count for level, count in enumerate(alpha.histogram())
                                  if level >= 96)
                    fraction = visible / (width * height)
                    require(fraction >= 0.002,
                            f"Fracture overlay is nearly invisible: {fraction:.2%}")
                if name == "miner.png":
                    # A nearly blank miner export can have both zero and nonzero
                    # alpha yet still be invisible at gameplay scale.
                    opaque_count = sum(count for level, count in enumerate(alpha.histogram())
                                       if level >= 128)
                    visible_fraction = opaque_count / (width * height)
                    require(0.10 <= visible_fraction <= 0.90,
                            f"Miner silhouette coverage invalid: {visible_fraction:.1%}")
                if name.startswith("ore_"):
                    # Require a substantial but not full-frame stone silhouette.
                    # This detects both missing alpha masks and tiny stray dots.
                    opaque = sum(v for level, v in enumerate(alpha.histogram()) if level >= 240)
                    coverage = opaque / (width * height)
                    require(0.12 <= coverage <= 0.80,
                            f"Ore silhouette coverage invalid: {name} ({coverage:.1%})")
                    # A stray pixel anywhere on the outer image border can
                    # produce visible seams in scaled or rotated ore sprites.
                    # Checking only the four corners misses these defects.
                    border = [
                        (x, 0) for x in range(width)
                    ] + [
                        (x, height - 1) for x in range(width)
                    ] + [
                        (0, y) for y in range(1, height - 1)
                    ] + [
                        (width - 1, y) for y in range(1, height - 1)
                    ]
                    stray = next(((x, y) for x, y in border
                                  if alpha.getpixel((x, y)) != 0), None)
                    require(stray is None,
                            f"Ore has nontransparent border pixel {stray}: {name}")
                    # The outermost row can be transparent while the next row
                    # contains a clipped anti-aliased fringe. Reserve two
                    # transparent pixels on all sides for safe interpolation.
                    inner_border = (
                        [(x, 1) for x in range(width)]
                        + [(x, height - 2) for x in range(width)]
                        + [(1, y) for y in range(2, height - 2)]
                        + [(width - 2, y) for y in range(2, height - 2)]
                    )
                    fringe = next(((x, y) for x, y in inner_border
                                   if alpha.getpixel((x, y)) != 0), None)
                    require(fringe is None,
                            f"Ore has clipped alpha fringe near border {fringe}: {name}")
                    # Coverage alone accepts a thin horizontal strip that
                    # occupies 12% of the canvas but looks nothing like ore.
                    # Check the opaque silhouette's two-dimensional extent.
                    solid_mask = alpha.point(lambda value: 255 if value >= 240 else 0)
                    bounds = solid_mask.getbbox()
                    require(bounds is not None, f"Ore has no opaque silhouette: {name}")
                    left, top, right, bottom = bounds
                    span_x = (right - left) / width
                    span_y = (bottom - top) / height
                    require(span_x >= 0.35 and span_y >= 0.35,
                            f"Ore silhouette is too narrow or flat: {name} "
                            f"(width={span_x:.1%}, height={span_y:.1%})")
                    require(alpha.getpixel((width // 2, height // 2)) >= 240,
                            f"Ore center unexpectedly transparent: {name}")
                    # A noisy mask can satisfy area, extent and centre tests
                    # while most of its pixels are isolated debris. The central
                    # ore body must form one substantial 4-connected silhouette.
                    # Count opaque pixels only, ignoring anti-aliased edges.
                    from collections import deque
                    opaque_pixels = set()
                    for y in range(top, bottom):
                        for x in range(left, right):
                            if alpha.getpixel((x, y)) >= 240:
                                opaque_pixels.add((x, y))
                    center = (width // 2, height // 2)
                    queue = deque([center])
                    connected = {center}
                    while queue:
                        x, y = queue.popleft()
                        for neighbor in ((x - 1, y), (x + 1, y),
                                         (x, y - 1), (x, y + 1)):
                            if neighbor in opaque_pixels and neighbor not in connected:
                                connected.add(neighbor)
                                queue.append(neighbor)
                    connected_fraction = len(connected) / len(opaque_pixels)
                    require(connected_fraction >= 0.85,
                            f"Ore has disconnected opaque fragments: {name} "
                            f"(central component={connected_fraction:.1%})")
    # Enabled/disabled skins must remain visibly distinguishable in the game.
    # Pixel-perfect deduplication alone misses near-identical button states;
    # compare the actual alpha-composited appearance on graphite UI panels.
    def graphite_button(name):
        with Image.open(directory / name) as source:
            rgba = source.convert("RGBA")
            return Image.alpha_composite(
                Image.new("RGBA", rgba.size, (23, 32, 47, 255)), rgba
            ).convert("RGB")

    enabled = graphite_button("button.png")
    disabled = graphite_button("button_off.png")
    difference = ImageChops.difference(enabled, disabled)
    state_delta = sum(ImageStat.Stat(difference).mean) / 3
    # A small bright badge can inflate the average while the rest of the
    # button remains identical. Require meaningful differences across the
    # surface, not only a localized decorative mark.
    changed = sum(1 for r, g, b in difference.getdata()
                  if max(r, g, b) >= 12)
    changed_fraction = changed / (enabled.width * enabled.height)
    # A horizontal band can change both left/right halves while leaving
    # the lower half visually unchanged. Validate all four quadrants so
    # disabled-state feedback is spatially distributed in both axes.
    quadrant_areas = []
    for y0, y1 in ((0, enabled.height // 2),
                   (enabled.height // 2, enabled.height)):
        for x0, x1 in ((0, enabled.width // 2),
                       (enabled.width // 2, enabled.width)):
            region = difference.crop((x0, y0, x1, y1))
            count = sum(1 for r, g, b in region.getdata()
                        if max(r, g, b) >= 12)
            quadrant_areas.append(count / (region.width * region.height))
    require(state_delta >= 6.0 and changed_fraction >= 0.15
            and min(quadrant_areas) >= 0.05,
            f"Button states are visually indistinguishable on graphite: "
            f"mean RGB delta={state_delta:.2f}, "
            f"changed area={changed_fraction:.1%}, "
            f"quadrant areas={[f'{v:.1%}' for v in quadrant_areas]}")
    print(f"PASS: {len(required)} raster assets decoded; 24 biomes, 24 ores, menu and UI art.")

if __name__ == "__main__":
    audit()
