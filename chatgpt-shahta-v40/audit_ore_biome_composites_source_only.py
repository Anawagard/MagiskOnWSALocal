"""Measure actual ore visibility against every biome backdrop (source-only).

Run after raster generation:
    python audit_ore_biome_composites_source_only.py --assets /path/to/shahta_v70

No Android build, asset modification, or workflow dispatch. Scores are relative
pixel contrast diagnostics, not a substitute for reviewing the five UI screens.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

COUNT = 24
BACKGROUND_SIZE = (360, 570)
ORE_SIZE = (300, 300)
SAMPLE_SIZE = 96

# Read directly from the v7.1 Java drawPage/drawMine rectangles. The biome
# fills (0,87,360,566) in page coordinates; the ore is drawn at
# (105,210,225,230). The global +60 translation cancels for both layers.
# These values are deliberately centralized to prevent diagnostics from
# measuring an unrelated 96px background patch.
BIOME_DEST = (0, 87, 360, 566)
ORE_DEST = (105, 210, 225, 230)


def ore_backdrop(scene, sample_size=SAMPLE_SIZE):
    """Sample the biome pixels actually underneath the rendered ore sprite."""
    if scene.size != BACKGROUND_SIZE:
        raise ValueError(f"Expected biome size {BACKGROUND_SIZE}, got {scene.size}")
    bx, by, bw, bh = BIOME_DEST
    ox, oy, ow, oh = ORE_DEST
    if bw <= 0 or bh <= 0 or ow <= 0 or oh <= 0:
        raise ValueError("Non-positive Java render rectangle")
    # PIL EXTENT maps the exact source-space rectangle to a square sample,
    # avoiding integer-rounded crop edges and preserving source registration.
    bounds = ((ox-bx)*scene.width/bw, (oy-by)*scene.height/bh,
              (ox+ow-bx)*scene.width/bw, (oy+oh-by)*scene.height/bh)
    if not (0 <= bounds[0] < bounds[2] <= scene.width and
            0 <= bounds[1] < bounds[3] <= scene.height):
        raise ValueError("Ore rectangle extends outside biome")
    return scene.transform((sample_size, sample_size), Image.Transform.EXTENT,
                           bounds, resample=Image.Resampling.BILINEAR)


def read_rgb(path, size, expected_format):
    with Image.open(path) as im:
        im.load()
        if im.format != expected_format or im.size != size:
            raise ValueError(f"{path.name}: expected {expected_format} {size}, got {im.format} {im.size}")
        return im.convert("RGB")


def read_ore(path, sample_size=SAMPLE_SIZE):
    with Image.open(path) as im:
        im.load()
        if im.format != "PNG" or im.size != ORE_SIZE:
            raise ValueError(f"{path.name}: expected PNG {ORE_SIZE}, got {im.format} {im.size}")
        if im.mode not in ("RGBA", "LA") and not (im.mode == "P" and "transparency" in im.info):
            raise ValueError(f"{path.name}: ore has no alpha channel")
        return im.convert("RGBA").resize((sample_size, sample_size), Image.Resampling.LANCZOS)


def contrast_score(background, ore):
    """Mean absolute displayed RGB difference, weighted by actual ore alpha."""
    bg = np.asarray(background, dtype=np.float32) / 255.0
    fg = np.asarray(ore, dtype=np.float32) / 255.0
    if bg.shape != fg.shape[:2] + (3,) or fg.shape[-1] != 4:
        raise ValueError("background and ore must have matching RGB/RGBA dimensions")
    alpha = fg[:, :, 3]
    visible = alpha > 0.0
    if not np.any(visible):
        raise ValueError("empty ore sprite")
    # Perceptual sRGB differences are a diagnostic proxy, not WCAG text contrast.
    delta = np.mean(np.abs(fg[:, :, :3] - bg), axis=2)
    # Ignore fully transparent RGB garbage; normalize only over visible pixels.
    # The displayed pixel difference is alpha * (foreground - background).
    return float(np.sum((delta * alpha)[visible]) / np.count_nonzero(visible))


def visibility_details(background, ore):
    """Measure coverage and the weakest visible tenth, not just mean contrast.

    The mean can hide low-contrast ore regions. A tenth-percentile score
    highlights patches that visually disappear against the current biome.
    Values are in displayed sRGB units [0, 1].
    """
    bg = np.asarray(background, dtype=np.float32) / 255.0
    fg = np.asarray(ore, dtype=np.float32) / 255.0
    if bg.shape != fg.shape[:2] + (3,) or fg.shape[-1] != 4:
        raise ValueError("background and ore must have matching RGB/RGBA dimensions")
    alpha = fg[:, :, 3]
    visible = alpha > 0.0
    if not np.any(visible):
        raise ValueError("empty ore sprite")
    displayed = np.mean(np.abs(fg[:, :, :3] - bg), axis=2) * alpha
    # Separate the opaque ore core from near-transparent antialiased edges.
    # Preserve existing metrics for backwards-compatible reports.
    core = alpha >= 0.5
    # Measure how much of the solid ore body nearly blends into the backdrop.
    # Fringe antialiasing must not inflate this fraction.
    core_low_contrast_fraction = (
        round(float(np.mean(displayed[core] < 0.08)), 6)
        if np.any(core) else None
    )
    return {
        "visible_coverage": round(float(np.mean(visible)), 6),
        "weakest_decile": round(float(np.percentile(displayed[visible], 10)), 6),
        "core_coverage": round(float(np.mean(core)), 6),
        # Mean contrast across the solid body complements the weakest decile:
        # a tiny dark patch should not be confused with a broadly muted ore.
        "core_mean_contrast": (
            round(float(np.mean(displayed[core])), 6)
            if np.any(core) else None
        ),
        "core_low_contrast_fraction": core_low_contrast_fraction,
        "core_weakest_decile": (
            round(float(np.percentile(displayed[core], 10)), 6)
            if np.any(core) else None
        ),
    }


def analyze(assets):
    assets = Path(assets)
    scenes = []
    ores = []
    for i in range(COUNT):
        scene = read_rgb(assets / f"biome_{i:02d}.jpg", BACKGROUND_SIZE, "JPEG")
        # Match the actual backdrop below the on-screen ore hitbox.
        scenes.append(ore_backdrop(scene))
        ores.append(read_ore(assets / f"ore_{i:02d}.png"))
    scores = []
    for i, scene in enumerate(scenes):
        for j, ore in enumerate(ores):
            scores.append({"biome": i + 1, "ore": j + 1,
                           "score": round(contrast_score(scene, ore), 6),
                           **visibility_details(scene, ore)})
    scores.sort(key=lambda row: (row["score"], row["biome"], row["ore"]))
    return scores


def summarize_risks(scores, low_contrast_threshold=0.08, affected_fraction=0.25, *, require_complete=False):
    """Rank actionable ore/biome visibility risks without hiding individual pairs.

    A risk means at least 25% of the alpha>=0.5 ore body has displayed
    channel difference below 0.08. These are diagnostics, not accessibility
    certification or proof of an in-game rendering defect.
    """
    if (not math.isfinite(low_contrast_threshold) or not math.isfinite(affected_fraction)
            or not 0 <= low_contrast_threshold <= 1
            or not 0 <= affected_fraction <= 1):
        raise ValueError("risk thresholds must be in [0, 1]")
    # A production risk report must contain all 576 unique measurements.
    # Tiny synthetic fixtures remain supported for focused unit tests.
    if require_complete:
        expected = {(i, j) for i in range(1, COUNT + 1)
                    for j in range(1, COUNT + 1)}
        if len(scores) != COUNT * COUNT:
            raise ValueError(f"Expected {COUNT * COUNT} biome/ore rows, got {len(scores)}")
        seen = set()
        for row in scores:
            if not isinstance(row, dict):
                raise ValueError("Non-dictionary biome/ore row")
            i, j = row.get("biome"), row.get("ore")
            if type(i) is not int or type(j) is not int or (i, j) not in expected or (i, j) in seen:
                raise ValueError(f"Invalid or duplicate biome/ore pair: {(i, j)}")
            seen.add((i, j))
            for key in ("score", "visible_coverage", "weakest_decile", "core_coverage"):
                value = row.get(key)
                if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError(f"Invalid {key} for {(i, j)}: {value}")
            for key in ("core_mean_contrast", "core_weakest_decile",
                        "core_low_contrast_fraction"):
                value = row.get(key)
                if row["core_coverage"] == 0:
                    if value is not None:
                        raise ValueError(f"Unexpected {key} without core for {(i, j)}")
                elif type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError(f"Missing/invalid {key} for {(i, j)}: {value}")
        if seen != expected:
            raise ValueError("Incomplete biome/ore matrix")
    # Fractions in scores were precomputed at the fixed 0.08 cutoff.
    # Accepting another cutoff would silently mislabel the risk report.
    if low_contrast_threshold != 0.08:
        raise ValueError("low_contrast_threshold must be 0.08 for precomputed scores")
    # A visible sprite with no alpha>=0.5 core cannot be classified as
    # low-risk: its core contrast is unmeasurable. Report it explicitly.
    unscorable = sorted(
        ({"biome": row["biome"], "ore": row["ore"]}
         for row in scores if row["core_low_contrast_fraction"] is None),
        key=lambda row: (row["biome"], row["ore"]),
    )
    risky = [
        row for row in scores
        if row["core_low_contrast_fraction"] is not None
        and row["core_low_contrast_fraction"] >= affected_fraction
    ]
    risky.sort(key=lambda row: (
        -row["core_low_contrast_fraction"], row["core_weakest_decile"],
        row["biome"], row["ore"]
    ))
    return {
        "threshold_displayed_difference": low_contrast_threshold,
        "threshold_affected_core_fraction": affected_fraction,
        "risk_pairs": len(risky),
        "unscorable_core_pairs": len(unscorable),
        "unscorable_core_locations": unscorable,
        # Identify whether missing opaque cores cluster in a particular
        # biome or ore. These counts are independent of the risk threshold.
        "unscorable_count_by_biome": {
            str(i): sum(row["biome"] == i for row in unscorable)
            for i in range(1, COUNT + 1)
        },
        "unscorable_count_by_ore": {
            str(i): sum(row["ore"] == i for row in unscorable)
            for i in range(1, COUNT + 1)
        },
        "worst_pairs": [
            {"biome": row["biome"], "ore": row["ore"],
             "affected_core_fraction": row["core_low_contrast_fraction"],
             "core_weakest_decile": row["core_weakest_decile"]}
            for row in risky
        ],
        "risk_count_by_biome": {
            str(i): sum(row["biome"] == i for row in risky)
            for i in range(1, COUNT + 1)
        },
        "risk_count_by_ore": {
            str(i): sum(row["ore"] == i for row in risky)
            for i in range(1, COUNT + 1)
        },
    }


def validate_diagnostic_destination(assets, output):
    """Keep diagnostic writes outside the entire production raster directory.

    A heatmap or contact sheet must never overwrite a menu, UI chrome, miner,
    fracture overlay, ore or biome. Resolve symlinks before checking ancestry.
    """
    assets_root = Path(assets).resolve()
    destination = Path(output).resolve()
    if destination == assets_root or assets_root in destination.parents:
        raise ValueError("Diagnostic output must be outside production assets")
    if destination.suffix.lower() != ".png":
        raise ValueError("Diagnostic output must have a .png extension")
    return destination


def render_risk_contact_sheet(assets, scores, output, limit=24):
    """Render actual high-risk ore over biome crops for visual review.

    The sheet is diagnostic only; it does not modify source art or game state.
    """
    from PIL import ImageDraw

    destination = validate_diagnostic_destination(assets, output)
    if not 1 <= limit <= COUNT * COUNT:
        raise ValueError("contact sheet limit must be in [1, 576]")

    risks = summarize_risks(scores, require_complete=True)
    # Include unscorable translucent sprites: otherwise a completely missing
    # opaque core is invisible in the visual review despite being flagged.
    # Reserve slots for both failure classes. Previously, 24+ missing-core
    # combinations could fill the sheet and hide every measurable risk.
    unscorable = [
        {**item, "affected_core_fraction": None}
        for item in risks["unscorable_core_locations"]
    ]
    measurable = risks["worst_pairs"]
    selected = []
    # Alternate categories when both exist, retaining each category's
    # deterministic risk ordering and never duplicating a pair.
    for index in range(max(len(unscorable), len(measurable))):
        if len(selected) >= limit:
            break
        if index < len(unscorable):
            selected.append(unscorable[index])
        if len(selected) >= limit:
            break
        if index < len(measurable):
            selected.append(measurable[index])
    if not selected:
        # A previous run's PNG must not masquerade as current risk evidence.
        destination.unlink(missing_ok=True)
        return 0
    tile = 128
    columns = min(6, len(selected))
    rows = (len(selected) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile, rows * (tile + 28)), (22, 27, 32))
    draw = ImageDraw.Draw(sheet)
    for index, item in enumerate(selected):
        biome, ore = item["biome"] - 1, item["ore"] - 1
        scene = read_rgb(Path(assets) / f"biome_{biome:02d}.jpg",
                         BACKGROUND_SIZE, "JPEG")
        background = ore_backdrop(scene, sample_size=tile)
        # Render the review tile directly from the 300px source rather than
        # upscaling the 96px analysis sample; preserve fine ore details.
        foreground = read_ore(Path(assets) / f"ore_{ore:02d}.png", sample_size=tile)
        # Composite exactly once in RGBA; do not apply the alpha twice.
        background = Image.alpha_composite(background.convert("RGBA"), foreground).convert("RGB")
        x, y = (index % columns) * tile, (index // columns) * (tile + 28)
        sheet.paste(background, (x, y))
        risk_label = ("NO CORE" if item["affected_core_fraction"] is None
                      else f"{item['affected_core_fraction']:.0%}")
        draw.text((x + 4, y + tile + 5),
                  f"B{biome + 1:02d} O{ore + 1:02d}  {risk_label}",
                  fill=(224, 245, 244))
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, format="PNG")
    return len(selected)



def render_visibility_heatmap(scores, output):
    """Plot all 576 ore/biome pairs, including translucent-core failures.

    Columns are ores 01..24, rows are biomes 01..24. A red tile indicates
    >=25% of the solid ore has low displayed contrast (<0.08); graphite
    denotes a healthy measured pair, and magenta means no measurable core.
    This is a diagnostic image, never a replacement for Android screenshots.
    """
    from PIL import ImageDraw

    expected = {(biome, ore) for biome in range(1, COUNT + 1)
                for ore in range(1, COUNT + 1)}
    actual = [(int(row["biome"]), int(row["ore"])) for row in scores]
    if len(actual) != COUNT * COUNT or set(actual) != expected:
        raise ValueError("Heatmap requires exactly 576 unique ore/biome pairs")
    destination = Path(output).resolve()
    if destination.suffix.lower() != ".png":
        raise ValueError("Heatmap output must have a .png extension")
    tile, left, top, right, bottom = 25, 70, 65, 22, 55
    canvas = Image.new("RGB", (left + COUNT * tile + right,
                               top + COUNT * tile + bottom), (17, 25, 37))
    draw = ImageDraw.Draw(canvas)
    for row in scores:
        biome, ore = int(row["biome"]), int(row["ore"])
        weak = row["core_low_contrast_fraction"]
        if weak is None:
            color = (195, 91, 192)
        elif weak >= 0.25:
            # Gradually hotter red as more of the ore becomes hard to see.
            heat = min(1.0, max(0.0, (weak - 0.25) / 0.75))
            color = (int(174 + 69 * heat), int(98 - 50 * heat),
                     int(75 - 37 * heat))
        else:
            # Cool, restrained teal for measured non-risky combinations.
            strength = max(0.0, min(1.0, 1.0 - weak / 0.25))
            color = (int(30 + 18 * strength), int(75 + 67 * strength),
                     int(88 + 46 * strength))
        x, y = left + (ore - 1) * tile, top + (biome - 1) * tile
        draw.rectangle((x + 1, y + 1, x + tile - 2, y + tile - 2), fill=color)
    for index in range(1, COUNT + 1):
        draw.text((left + (index - 1) * tile + 3, top - 19),
                  f"{index:02d}", fill=(211, 226, 227))
        draw.text((left - 30, top + (index - 1) * tile + 5),
                  f"{index:02d}", fill=(211, 226, 227))
    draw.text((left, 12), "ORE ->", fill=(131, 229, 217))
    draw.text((left, top + COUNT * tile + 8),
              "TEAL: measurable  RED: low contrast  MAGENTA: no solid core",
              fill=(211, 226, 227))
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Save to a temporary sibling, then replace atomically to avoid a
    # truncated diagnostic being mistaken for a complete visibility matrix.
    import os
    import tempfile
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".shahta-heatmap-", suffix=".png",
            dir=destination.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
        canvas.save(temporary, format="PNG")
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--risk-sheet", type=Path, help="optional PNG contact sheet of worst ore/biome pairs")
    parser.add_argument("--heatmap", type=Path, help="optional full 24x24 PNG visibility heatmap")
    args = parser.parse_args()
    if not 1 <= args.limit <= COUNT * COUNT:
        parser.error("--limit must be in [1, 576]")
    if args.risk_sheet is not None:
        validate_diagnostic_destination(args.assets, args.risk_sheet)
    if args.heatmap is not None:
        validate_diagnostic_destination(args.assets, args.heatmap)
    scores = analyze(args.assets)
    # The mean can hide large low-contrast patches in an otherwise bright ore.
    # Keep the historical ranking while also reporting the weakest solid cores.
    core_scores = [row for row in scores if row["core_weakest_decile"] is not None]
    core_scores.sort(key=lambda row: (
        row["core_weakest_decile"], row["biome"], row["ore"]
    ))
    missing_cores = [
        {"biome": row["biome"], "ore": row["ore"]}
        for row in scores if row["core_weakest_decile"] is None
    ]
    risk_summary = summarize_risks(scores, require_complete=True)
    if args.risk_sheet is not None:
        render_risk_contact_sheet(args.assets, scores, args.risk_sheet, args.limit)
    if args.heatmap is not None:
        render_visibility_heatmap(scores, args.heatmap)
    risk_summary["worst_pairs"] = risk_summary["worst_pairs"][:args.limit]
    print(json.dumps({
        "pairs": len(scores),
        "lowest_contrast": scores[:args.limit],
        "lowest_core_contrast": core_scores[:args.limit],
        "missing_opaque_cores": missing_cores,
        "visibility_risks": risk_summary,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
