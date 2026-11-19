"""Check cross-category tint collisions in the existing 24x24 raster palettes.

Pure source audit: no Android project, images, or build processes are touched.
"""
from audit_palette_perception_source_only import palettes, oklab
from math import dist


def blend_srgb(background, foreground, alpha):
    """Approximate displayed RGB when an ore tint overlays its biome tint."""
    if not isinstance(alpha, (int, float)) or isinstance(alpha, bool) or not 0 <= alpha <= 1:
        raise ValueError("alpha must be in [0, 1]")
    # Reject malformed RGB rather than silently truncating zip() or producing
    # out-of-range colors. This diagnostic must never mask asset corruption.
    for name, rgb in (("background", background), ("foreground", foreground)):
        if not isinstance(rgb, (tuple, list)) or len(rgb) != 3:
            raise ValueError(f"{name} must contain exactly three RGB channels")
        if any(type(channel) is not int or not 0 <= channel <= 255 for channel in rgb):
            raise ValueError(f"{name} RGB channels must be integers in [0, 255]")
    return tuple(round((1 - alpha) * bg + alpha * fg)
                 for bg, fg in zip(background, foreground))


def composited_palette_collisions(alpha=0.65, limit=10):
    """Rank ore/biome tint collisions after alpha compositing (not a pixel audit)."""
    if type(limit) is not int or not 1 <= limit <= 576:
        raise ValueError("limit must be an integer in [1, 576]")
    colors = palettes()
    return sorted(
        (dist(oklab(scene), oklab(blend_srgb(scene, ore, alpha))), i, j)
        for i, scene in enumerate(colors["SCENES"])
        for j, ore in enumerate(colors["ORES"])
    )[:limit]



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
        print(f"biome {biome + 1:02d} / ore {ore + 1:02d}: OKLab {distance:.4f}")
    print("Composited tint risk at alpha=0.65 (illustrative, not actual sprite opacity):")
    for distance, biome, ore in composited_palette_collisions():
        print(f"biome {biome + 1:02d} / ore {ore + 1:02d}: OKLab {distance:.4f}")
    print("Tint-only diagnostic; inspect real textures before changing palettes.")
