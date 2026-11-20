"""Measure actual ore visibility against every biome backdrop (source-only).

Run after raster generation:
    python audit_ore_biome_composites_source_only.py --assets /path/to/shahta_v70

No Android build, asset modification, or workflow dispatch. Scores are relative
pixel contrast diagnostics, not a substitute for reviewing the five UI screens.
"""
import argparse
import json
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
    # Measure how much of the solid ore body nearly blends into the backdrop.\n    # Fringe antialiasing must not inflate this fraction.\n    core_low_contrast_fraction = (\n        round(float(np.mean(displayed[core] < 0.08)), 6)\n        if np.any(core) else None\n    )\n    return {
        "visible_coverage": round(float(np.mean(visible)), 6),
        "weakest_decile": round(float(np.percentile(displayed[visible], 10)), 6),
        "core_coverage": round(float(np.mean(core)), 6),\n        "core_low_contrast_fraction": core_low_contrast_fraction,
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=15)
    args = parser.parse_args()
    if not 1 <= args.limit <= COUNT * COUNT:
        parser.error("--limit must be in [1, 576]")
    scores = analyze(args.assets)
    print(json.dumps({"pairs": len(scores), "lowest_contrast": scores[:args.limit]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
