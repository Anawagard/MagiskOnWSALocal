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
    # Bind the JSON audit to the actual bytes on disk. An internally
    # consistent report can otherwise pass after assets have been replaced,
    # truncated or swapped since the audit was generated.
    import hashlib
    for group, prefix, suffix in (
        ("biomes", "biome", ".jpg"), ("ores", "ore", ".png")
    ):
        expected_names = {f"{prefix}_{i:02d}{suffix}" for i in range(24)}
        entries = data[group]
        reported_names = [entry["file"] for entry in entries]
        if set(reported_names) != expected_names or len(reported_names) != 24:
            raise ValueError(f"{group}: report filenames do not match the 24 expected assets")
        for entry in entries:
            asset = assets / entry["file"]
            if not asset.is_file():
                raise ValueError(f"{group}: missing audited asset {asset.name}")
            actual_hash = hashlib.sha256(asset.read_bytes()).hexdigest()
            if actual_hash != entry["sha256"]:
                raise ValueError(f"{group}: stale or tampered audit for {asset.name}")
            with Image.open(asset) as img:
                img.load()
                if list(img.size) != entry["size"]:
                    raise ValueError(f"{group}: stale dimensions for {asset.name}")
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
    # A valid PNG header does not guarantee a useful review sheet: an empty
    # canvas or a tiny thumbnail can pass Image.verify() unnoticed.
    from PIL import ImageStat
    for group in ("biomes", "ores", "interface"):
        path = sheets / f"shahta_{group}_contact_sheet.png"
        with Image.open(path) as img:
            img.load()
            if img.format != "PNG" or img.width < 300 or img.height < 200:
                raise ValueError(f"{path.name}: invalid contact-sheet format or size")
            preview = img.convert("RGB")
            if max(ImageStat.Stat(preview).var) < 2.0:
                raise ValueError(f"{path.name}: blank or visually flat contact sheet")
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
