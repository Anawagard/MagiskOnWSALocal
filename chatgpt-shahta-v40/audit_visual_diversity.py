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
        if source.width < 128 or source.height < 128:
            raise ValueError(f"{path.name}: raster too small")
        if ore and source.mode not in ("RGBA", "LA", "P"):
            raise ValueError(f"{path.name}: ore requires alpha-capable image")
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
    thumb = rgba.convert("RGB").resize((32, 32), Image.Resampling.BILINEAR)
    pixels = np.asarray(thumb, dtype=np.float32)
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
        for i in range(len(thumbs)):
            for j in range(i + 1, len(thumbs)):
                mean_delta = float(np.mean(np.abs(thumbs[i] - thumbs[j])))
                if mean_delta < 1.5:
                    raise ValueError(
                        f"{label}: visually duplicated {names[i]} / {names[j]} "
                        f"(mean RGB delta {mean_delta:.2f})"
                    )
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
