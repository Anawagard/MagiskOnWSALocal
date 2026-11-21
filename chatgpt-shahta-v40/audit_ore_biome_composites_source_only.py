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


def read_rgb(path, size, expected_format):
    with Image.open(path) as im:
        im.load()
        if im.format != expected_format or im.size != size:
            raise ValueError(f"{path.name}: expected {expected_format} {size}, got {im.format} {im.size}")
        return im.convert("RGB")


def read_ore(path):
    with Image.open(path) as im:
        im.load()
        if im.format != "PNG" or im.size != ORE_SIZE:
            raise ValueError(f"{path.name}: expected PNG {ORE_SIZE}, got {im.format} {im.size}")
        if im.mode not in ("RGBA", "LA") and not (im.mode == "P" and "transparency" in im.info):
            raise ValueError(f"{path.name}: ore has no alpha channel")
        return im.convert("RGBA").resize((SAMPLE_SIZE, SAMPLE_SIZE), Image.Resampling.LANCZOS)


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
        # The gameplay corridor is central. Use the same fixed crop for all
        # biomes to avoid ranking unrelated decorative side-wall details.
        crop = scene.crop((132, 200, 228, 296))
        scenes.append(crop)
        ores.append(read_ore(assets / f"ore_{i:02d}.png"))
    scores = []
    for i, scene in enumerate(scenes):
        for j, ore in enumerate(ores):
            scores.append({"biome": i + 1, "ore": j + 1,
                           "score": round(contrast_score(scene, ore), 6),
                           **visibility_details(scene, ore)})
    scores.sort(key=lambda row: (row["score"], row["biome"], row["ore"]))
    return scores


def summarize_risks(scores, low_contrast_threshold=0.08, affected_fraction=0.25):
    """Rank actionable ore/biome visibility risks without hiding individual pairs.

    A risk means at least 25% of the alpha>=0.5 ore body has displayed
    channel difference below 0.08. These are diagnostics, not accessibility
    certification or proof of an in-game rendering defect.
    """
    if (not math.isfinite(low_contrast_threshold) or not math.isfinite(affected_fraction)
            or not 0 <= low_contrast_threshold <= 1
            or not 0 <= affected_fraction <= 1):
        raise ValueError("risk thresholds must be in [0, 1]")
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


def render_risk_contact_sheet(assets, scores, output, limit=24):
    """Render actual high-risk ore over biome crops for visual review.

    The sheet is diagnostic only; it does not modify source art or game state.
    """
    from PIL import ImageDraw

    risks = summarize_risks(scores)
    selected = risks["worst_pairs"][:limit]
    if not selected:
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
        background = scene.crop((132, 200, 228, 296)).resize((tile, tile))
        foreground = read_ore(Path(assets) / f"ore_{ore:02d}.png").resize(
            (tile, tile), Image.Resampling.LANCZOS)
        background.paste(foreground, (0, 0), foreground)
        x, y = (index % columns) * tile, (index // columns) * (tile + 28)
        sheet.paste(background, (x, y))
        draw.text((x + 4, y + tile + 5),
                  f"B{biome + 1:02d} O{ore + 1:02d}  {item['affected_core_fraction']:.0%}",
                  fill=(224, 245, 244))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="PNG")
    return len(selected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--risk-sheet", type=Path, help="optional PNG contact sheet of worst ore/biome pairs")
    args = parser.parse_args()
    if not 1 <= args.limit <= COUNT * COUNT:
        parser.error("--limit must be in [1, 576]")
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
    risk_summary = summarize_risks(scores)
    if args.risk_sheet is not None:
        render_risk_contact_sheet(args.assets, scores, args.risk_sheet, args.limit)
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
