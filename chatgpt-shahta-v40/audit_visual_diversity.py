"""Source-only visual quality gate for the 48 game-world rasters.

Run after generate_art_v70.py, before the single final Android build:
    python audit_visual_diversity.py --assets /path/to/shahta_v70

This never modifies assets or invokes Gradle. It checks actual decoded pixels,
not filenames, and fails closed on missing/blank/near-identical artwork.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

BIOMES = [f"biome_{i:02d}.jpg" for i in range(24)]
ORES = [f"ore_{i:02d}.png" for i in range(24)]


def inspect(path, ore):
    with Image.open(path) as source:
        source.load()
        # Extensions alone do not establish decoder compatibility: a PNG
        # renamed .jpg can slip into the Android resource pack and silently
        # change memory/compression assumptions.
        expected_format = "PNG" if ore else "JPEG"
        if source.format != expected_format:
            raise ValueError(
                f"{path.name}: expected {expected_format} encoding, "
                f"got {source.format}"
            )
        # The Android renderer assumes portrait 360x570 biome backdrops and
        # square 300x300 ore icons. A large but wrongly shaped raster can pass
        # the pixel-diversity checks while stretching badly on narrow phones.
        expected = (300, 300) if ore else (360, 570)
        if source.size != expected:
            raise ValueError(
                f"{path.name}: expected {expected[0]}x{expected[1]} raster, "
                f"got {source.width}x{source.height}"
            )
        if ore and source.mode not in ("RGBA", "LA", "P"):
            raise ValueError(f"{path.name}: ore requires alpha-capable image")
        if ore and source.mode == "P" and "transparency" not in source.info:
            raise ValueError(f"{path.name}: palette image has no transparency")
        rgba = source.convert("RGBA")
        arr = np.asarray(rgba, dtype=np.uint8)
    alpha = arr[:, :, 3]
    if ore:
        occupancy = float(np.mean(alpha > 16))
        if not 0.12 <= occupancy <= 0.85:
            raise ValueError(f"{path.name}: ore alpha occupancy {occupancy:.3f}")
        if np.min(alpha) > 16 or np.max(alpha) < 240:
            raise ValueError(f"{path.name}: missing transparent or opaque pixels")
        visible = arr[:, :, :3][alpha > 16]
    else:
        visible = arr[:, :, :3].reshape(-1, 3)
        occupancy = 1.0
    if np.mean(np.std(visible.astype(np.float32), axis=0)) < 8:
        raise ValueError(f"{path.name}: insufficient tonal variation")
    # Fixed-size visual fingerprint, compared across the same asset family.
    # Composite on a fixed graphite background to avoid treating fully
    # transparent RGB payload as visible ore texture. Keep alpha as a
    # separate channel so distinct silhouettes cannot look identical.
    if ore:
        # Composite at native resolution *before* downsampling. Resizing
        # straight-alpha RGBA can mix invisible RGB payload into edge pixels,
        # producing false differences between visually identical sprites.
        background = Image.new("RGB", rgba.size, (19, 27, 36))
        background.paste(rgba, mask=rgba.getchannel("A"))
        rgb = np.asarray(
            background.resize((32, 32), Image.Resampling.BILINEAR),
            dtype=np.float32,
        )
        alpha_thumb = np.asarray(
            rgba.getchannel("A").resize((32, 32), Image.Resampling.BILINEAR),
            dtype=np.float32,
        )
        pixels = np.concatenate((rgb, alpha_thumb[:, :, None]), axis=2)
    else:
        pixels = np.asarray(
            rgba.convert("RGB").resize((32, 32), Image.Resampling.BILINEAR),
            dtype=np.float32,
        )
    return {
        "file": path.name,
        "size": list(arr.shape[1::-1]),
        "alpha_occupancy": round(occupancy, 4),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }, pixels


def audit(folder):
    result = {"biomes": [], "ores": []}
    for label, names, ore in (("biomes", BIOMES, False), ("ores", ORES, True)):
        thumbs = []
        for name in names:
            path = folder / name
            if not path.is_file():
                raise FileNotFoundError(path)
            entry, thumb = inspect(path, ore)
            result[label].append(entry)
            thumbs.append(thumb)
        # Reject identical and almost-identical images even when encoded
        # with different metadata. This is not a subjective art-quality score.
        closest_pair = None
        minimum_delta = float("inf")
        # Keep each asset's nearest visual neighbor in the review report.
        # A single global closest pair can hide repeated visual motifs across
        # the other 22 images, even when the hard duplicate gate passes.
        nearest = [None] * len(names)
        distances = [float("inf")] * len(names)
        for i in range(len(thumbs)):
            for j in range(i + 1, len(thumbs)):
                mean_delta = float(np.mean(np.abs(thumbs[i] - thumbs[j])))
                if mean_delta < minimum_delta:
                    minimum_delta = mean_delta
                    closest_pair = (names[i], names[j])
                for index, neighbor in ((i, j), (j, i)):
                    if mean_delta < distances[index]:
                        distances[index] = mean_delta
                        nearest[index] = names[neighbor]
                if mean_delta < 1.5:
                    raise ValueError(
                        f"{label}: visually duplicated {names[i]} / {names[j]} "
                        f"(mean visible-channel delta {mean_delta:.2f})"
                    )
        result[f"{label}_nearest_neighbors"] = [
            {
                "file": name,
                "nearest_file": nearest[i],
                "mean_channel_delta": round(distances[i], 3),
            }
            for i, name in enumerate(names)
        ]
        # Include the closest pair in successful reports so art reviewers can
        # inspect borderline similarities rather than treating pass as proof
        # of artistic distinctness. This adds metadata without changing assets.
        result[f"{label}_closest_pair"] = {
            "files": list(closest_pair),
            "mean_channel_delta": round(minimum_delta, 3),
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = audit(args.assets)
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
