"""Source-only overview of menu backgrounds and HUD skins for visual review.

Usage: python preview_ui_skins.py ASSET_DIRECTORY OUTPUT_PNG
Never invokes Gradle, Android or Actions. Requires Pillow.
"""
import argparse
import os
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ASSETS = (
    ("menu_1.jpg", (360, 570)),
    ("menu_2.jpg", (360, 570)),
    ("menu_3.jpg", (360, 570)),
    ("menu_4.jpg", (360, 570)),
    ("panel.png", (400, 96)),
    ("button.png", (160, 64)),
    ("button_off.png", (160, 64)),
    ("header.png", (360, 88)),
    ("nav.png", (360, 50)),
)
BG = (17, 25, 37)
INK = (109, 229, 216)


def build_preview(assets: Path, target: Path) -> Path:
    assets, target = assets.resolve(), target.resolve()
    if not assets.is_dir():
        raise ValueError("Asset directory must exist")
    if target.parent == assets or assets in target.parents:
        raise ValueError("Preview must be written outside the asset directory")
    if not target.parent.is_dir():
        raise ValueError("Preview output directory must exist")
    # Validate the complete set before writing a preview; avoid hiding missing
    # Android resources behind a partially successful contact sheet.
    for name, expected in ASSETS:
        path = assets / name
        if not path.is_file():
            raise FileNotFoundError(path)
        with Image.open(path) as im:
            fmt = "JPEG" if name.endswith(".jpg") else "PNG"
            if im.format != fmt or im.size != expected:
                raise ValueError(f"{name}: expected {fmt} {expected}, got {im.format} {im.size}")
            im.verify()

    sheet = Image.new("RGB", (1040, 1020), BG)
    draw = ImageDraw.Draw(sheet)
    for i, (name, _) in enumerate(ASSETS):
        if i < 4:
            x, y, w, h = 12 + i * 256, 12, 244, 620
        else:
            j = i - 4
            x, y, w, h = 12, 654 + j * 72, 1016, 52
        with Image.open(assets / name) as im:
            rgba = im.convert("RGBA")
            matte = Image.new("RGBA", rgba.size, (*BG, 255))
            composite = Image.alpha_composite(matte, rgba).convert("RGB")
            # Preserve aspect ratio: cropping can hide clipped decorative UI.
            thumbnail = ImageOps.contain(composite, (w, h), Image.Resampling.LANCZOS)
            sheet.paste(thumbnail, (x + (w-thumbnail.width)//2, y))
        draw.rectangle((x, y, x+w-1, y+h-1), outline=(65, 93, 105))
        draw.text((x+5, y+h+3), name, fill=INK)
    # Save only after all sources have decoded successfully.
    # Preserve a previous successful audit if encoding fails mid-write.
    # Same-directory replacement is atomic on normal local filesystems.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".shahta-ui-", suffix=".png", dir=target.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
        sheet.save(temporary, format="PNG", optimize=True)
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("assets", type=Path)
    parser.add_argument("output_png", type=Path)
    args = parser.parse_args()
    print(build_preview(args.assets, args.output_png))


if __name__ == "__main__":
    main()
