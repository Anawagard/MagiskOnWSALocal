"""Source-only perceptual palette audit for Shahta's 24 biomes and 24 ores.

Reads literal palette tuples from the generator AST; never imports the generator,
restores Android sources, writes assets, or invokes Gradle. Run directly with Python.
"""
import ast
import math
from pathlib import Path

SOURCE = Path(__file__).with_name("generate_art_v70.py")
GRAPHITE = (23, 32, 47)


def palettes(source=SOURCE):
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("SCENES", "ORES"):
                    found[target.id] = ast.literal_eval(node.value)
    if set(found) != {"SCENES", "ORES"}:
        raise ValueError("Both literal palettes are required")
    for name, colors in found.items():
        validate_palette(name, colors)
    return found


def validate_palette(name, colors):
    """Reject malformed entries before hashing or measuring color distance."""
    if not isinstance(colors, (list, tuple)) or len(colors) != 24:
        raise ValueError(f"{name}: expected exactly 24 RGB entries")
    for index, color in enumerate(colors):
        if (not isinstance(color, (list, tuple)) or len(color) != 3
                or any(type(v) is not int or not 0 <= v <= 255 for v in color)):
            raise ValueError(f"{name}[{index}]: invalid RGB triplet")
    if len({tuple(color) for color in colors}) != 24:
        raise ValueError(f"{name}: duplicate RGB entries")


def srgb_channel(v):
    v = v / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = (srgb_channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    light, dark = sorted((luminance(a), luminance(b)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def oklab(rgb):
    r, g, b = (srgb_channel(v) for v in rgb)
    l = 0.4122214708*r + 0.5363325363*g + 0.0514459929*b
    m = 0.2119034982*r + 0.6806995451*g + 0.1073969566*b
    s = 0.0883024619*r + 0.2817188376*g + 0.6299787005*b
    l, m, s = l**(1/3), m**(1/3), s**(1/3)
    return (0.2104542553*l + 0.7936177850*m - 0.0040720468*s,
            1.9779984951*l - 2.4285922050*m + 0.4505937099*s,
            0.0259040371*l + 0.7827717662*m - 0.8086757660*s)


def audit():
    for name, colors in palettes().items():
        labs = [oklab(color) for color in colors]
        pairs = sorted((math.dist(labs[i], labs[j]), i, j)
                       for i in range(24) for j in range(i + 1, 24))
        contrasts = sorted((contrast(color, GRAPHITE), i)
                           for i, color in enumerate(colors))
        print(f"{name}: 24 unique colors; nearest OKLab pairs:")
        for distance, i, j in pairs[:5]:
            print(f"  {i:02d}/{j:02d}: distance={distance:.4f} "
                  f"RGB={colors[i]}/{colors[j]}")
        print(f"  Lowest graphite contrast: "
              f"{contrasts[0][0]:.2f}:1 (index {contrasts[0][1]:02d})")
        # Palette colors are material tints, NOT UI text. Report contrast
        # for design review; do not impose WCAG text thresholds on artwork.


if __name__ == "__main__":
    audit()
