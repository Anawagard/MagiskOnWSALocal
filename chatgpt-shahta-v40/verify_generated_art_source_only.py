"""Run the real 48-image art pipeline without restoring Android or building an APK.

Usage: python verify_generated_art_source_only.py
Requires Pillow and numpy. Uses temporary directories only; does not touch
Android project files, workflows, signing keys, or game saves.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent


def run(script, *args, env=None):
    subprocess.run(
        [sys.executable, str(HERE / script), *map(str, args)],
        check=True, cwd=HERE, env=env,
    )


def verify(root):
    """Generate and inspect real assets inside an isolated output directory."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise ValueError(f"Refusing to overwrite a nonempty art directory: {root}")
    # Avoid mixing new rasters with stale previews from a previous run.
    # This directory contains only generated art and audit artifacts.
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")
    assets = root / "assets"
    sheets = root / "sheets"
    assets.mkdir()
    sheets.mkdir()
    env = os.environ.copy()
    env["SHAHTA_ART_PREVIEW_DIR"] = str(assets)
    env.pop("SHAHTA_ART_PROJECT", None)
    run("generate_art_v70.py", env=env)
    report = root / "visual_audit.json"
    run("audit_visual_diversity.py", "--assets", assets,
        "--report", report)
    run("render_art_contact_sheet.py", "--assets", assets,
        "--output", sheets)
    import json
    data = json.loads(report.read_text(encoding="utf-8"))
    # Reject malformed or mathematically inconsistent similarity metadata.
    from test_visual_audit_report_integrity_source_only import validate_report
    validate_report(data)
    if len(data["biomes"]) != 24 or len(data["ores"]) != 24:
        raise ValueError("Visual audit must contain exactly 24 biomes and 24 ores")
    for name in ("biomes", "ores"):
        entries = data[name]
        if len({item["sha256"] for item in entries}) != 24:
            raise ValueError(f"{name}: duplicate file hashes")
        neighbors = data[f"{name}_nearest_neighbors"]
        if len(neighbors) != 24:
            raise ValueError(f"{name}: incomplete nearest-neighbor report")
        if not all(item["nearest_file"] != item["file"] for item in neighbors):
            raise ValueError(f"{name}: invalid self-neighbor")
    # Verify all UI skins and menu backdrops, not just the ore/biome subset.
    # The contact-sheet generator checks readability, but explicit image
    # dimensions and alpha rules prevent accidentally publishing empty skins.
    ui_files = ("panel.png", "button.png", "button_off.png", "header.png",
                "nav.png", "fractures.png", "miner.png")
    for filename in (*ui_files, *(f"menu_{i}.jpg" for i in range(1, 5))):
        path = assets / filename
        with Image.open(path) as img:
            img.load()
            if img.width < 16 or img.height < 16:
                raise ValueError(f"{filename}: undersized interface raster")
            if filename.endswith(".jpg") and img.format != "JPEG":
                raise ValueError(f"{filename}: menu backdrop is not JPEG")
            if filename.endswith(".png") and img.format != "PNG":
                raise ValueError(f"{filename}: UI skin is not PNG")
            # A syntactically valid transparent PNG can still be invisible.
            # Verify the actual composited pixel coverage, not file size.
            if filename.endswith(".png"):
                alpha = img.convert("RGBA").getchannel("A")
                if alpha.getbbox() is None:
                    raise ValueError(f"{filename}: fully transparent UI raster")
                # Nonempty alpha alone is insufficient: a single opaque pixel
                # can pass the old gate while the control remains invisible.
                # Check visible coverage and composited tonal variation using
                # the same graphite surface as the in-game chrome.
                import numpy as np
                from PIL import ImageStat
                alpha_pixels = np.asarray(alpha, dtype=np.uint8)
                coverage = float(np.mean(alpha_pixels > 16))
                if coverage < 0.02:
                    raise ValueError(
                        f"{filename}: insufficient visible UI coverage "
                        f"({coverage:.3%})"
                    )
                graphite = Image.new("RGB", img.size, (19, 27, 36))
                rgba = img.convert("RGBA")
                graphite.paste(rgba, mask=rgba.getchannel("A"))
                if max(ImageStat.Stat(graphite).var) < 1.0:
                    raise ValueError(f"{filename}: visually flat UI raster")
            else:
                # Detect blank/solid JPEG menu backdrops before release.
                from PIL import ImageStat
                variance = ImageStat.Stat(img.convert("RGB")).var
                if max(variance) < 2.0:
                    raise ValueError(f"{filename}: visually flat menu backdrop")
    for group in ("biomes", "ores", "interface"):
        path = sheets / f"shahta_{group}_contact_sheet.png"
        with Image.open(path) as img:
            img.verify()
    print(f"PASS: 24 generated biomes, 24 generated ores, diversity audit, "
          f"and 3 real contact sheets at {root} (source-only; no Android build)")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path,
        help="Keep all 48 generated assets, JSON report, and 3 contact sheets "
             "in this NEW or EMPTY directory for visual review. "
             "Without this flag, temporary files are deleted.",
    )
    args = parser.parse_args()
    if args.output is None:
        with tempfile.TemporaryDirectory(prefix="shahta-real-art-") as tmp:
            verify(Path(tmp))
    else:
        verify(args.output.expanduser().resolve())



if __name__ == "__main__":
    main()
