"""Check cross-category tint collisions in the existing 24x24 raster palettes.

Pure source audit: no Android project, images, or build processes are touched.
"""
from audit_palette_perception_source_only import palettes, oklab
from math import dist


def cross_palette_collisions(limit=10):
    if type(limit) is not int or not 1 <= limit <= 576:
        raise ValueError("limit must be an integer in [1, 576]")
    colors = palettes()
    scenes = [oklab(rgb) for rgb in colors["SCENES"]]
    ores = [oklab(rgb) for rgb in colors["ORES"]]
    return sorted(
        (dist(scene, ore), i, j)
        for i, scene in enumerate(scenes)
        for j, ore in enumerate(ores)
    )[:limit]


if __name__ == "__main__":
    for distance, biome, ore in cross_palette_collisions():
        print(f"biome {biome:02d} / ore {ore:02d}: OKLab {distance:.4f}")
    print("Tint-only diagnostic; inspect real textures before changing palettes.")
