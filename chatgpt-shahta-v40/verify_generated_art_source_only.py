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
    """Bound every source-only stage and keep Python assertions enabled."""
    safe_env = dict(os.environ if env is None else env)
    safe_env.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
        "PYTHONOPTIMIZE": "",
    })
    subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE / script), *map(str, args)],
        check=True, cwd=HERE, env=safe_env, timeout=300,
    )


def verify(root):
    """Generate and inspect real assets inside an isolated output directory."""
    root = Path(root)
    # Never follow an output-directory symlink: a seemingly empty alias can
    # redirect generated rasters and audit files outside the requested path.
    # Check before mkdir, since exist_ok=True accepts directory symlinks.
    # Reject symlinks in every existing ancestor too: checking only the leaf
    # misses paths such as alias/new-output where alias points elsewhere.
    if any(part.is_symlink() for part in (root, *root.parents)):
        raise ValueError(f"Refusing symlinked art output directory or parent: {root}")
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
    # Audit all 24 x 24 *displayed* ore/biome combinations using the exact
    # Java render registration. Keep the diagnostics outside the asset pack.
    # This stage runs on the real generated rasters, never an Android build.
    run("audit_ore_biome_composites_source_only.py",
        "--assets", assets,
        "--risk-sheet", sheets / "shahta_ore_biome_risks.png",
        "--heatmap", sheets / "shahta_ore_biome_heatmap.png")
    for diagnostic in ("shahta_ore_biome_heatmap.png",
                       "shahta_ore_biome_risks.png"):
        image_path = sheets / diagnostic
        if not image_path.is_file():
            # The risk sheet may legitimately be absent when no pairs are
            # flagged; the 576-cell heatmap must always be present.
            if diagnostic.endswith("risks.png"):
                continue
            raise ValueError(f"Missing ore/biome matrix diagnostic: {diagnostic}")
        with Image.open(image_path) as matrix_image:
            matrix_image.load()
            if matrix_image.format != "PNG" or min(matrix_image.size) < 300:
                raise ValueError(f"Invalid ore/biome diagnostic: {diagnostic}")
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
                expected_format = "JPEG" if group == "biomes" else "PNG"
                if img.format != expected_format:
                    raise ValueError(
                        f"{group}: {asset.name} contains {img.format}, "
                        f"expected {expected_format}"
                    )
                expected_size = (360, 570) if group == "biomes" else (300, 300)
                if img.size != expected_size:
                    raise ValueError(
                        f"{group}: {asset.name} has {img.size}, expected {expected_size}"
                    )
                if list(img.size) != entry["size"]:
                    raise ValueError(f"{group}: stale dimensions for {asset.name}")
                # Compare reported opacity with the decoded image pixels.
                import numpy as np
                rgba = np.asarray(img.convert("RGBA"), dtype=np.uint8)
                # Match audit_visual_diversity.inspect(): antialiased fringe alpha
                # values 1..16 are intentionally excluded from visible coverage.
                actual_occupancy = float(np.mean(rgba[:, :, 3] > 16))
                if abs(actual_occupancy - entry["alpha_occupancy"]) > 0.001:
                    raise ValueError(
                        f"{group}: stale alpha occupancy for {asset.name}"
                    )
                # A self-consistent report must not excuse a nearly invisible ore.
                # JPEG backgrounds must be fully opaque by construction.
                if group == "biomes" and actual_occupancy != 1.0:
                    raise ValueError(f"{group}: nonopaque biome {asset.name}")
                if group == "ores" and not 0.05 <= actual_occupancy <= 0.95:
                    raise ValueError(
                        f"{group}: implausible ore silhouette coverage "
                        f"for {asset.name}: {actual_occupancy:.2%}"
                    )
                # A valid occupancy ratio can still hide a cropped ore:
                # transparent sprite margins must survive scaling on narrow
                # displays. Reject any visible pixels touching the canvas edge.
                if group == "ores":
                    alpha = rgba[:, :, 3]
                    border = np.concatenate((
                        alpha[0, :], alpha[-1, :],
                        alpha[1:-1, 0], alpha[1:-1, -1],
                    ))
                    if np.any(border > 16):
                        raise ValueError(
                            f"{group}: cropped silhouette touches sprite border "
                            f"in {asset.name}"
                        )
                # Unique hashes alone cannot establish texture quality.
                # Exclude transparent ore margins from color statistics.
                rgb = rgba[:, :, :3].astype(np.float32)
                visible = rgba[:, :, 3] > 16
                samples = rgb[visible] if group == "ores" else rgb.reshape(-1, 3)
                if samples.shape[0] < 100:
                    raise ValueError(f"{group}: too few visible pixels in {asset.name}")
                channel_variance = np.var(samples, axis=0)
                if float(np.max(channel_variance)) < 12.0:
                    raise ValueError(
                        f"{group}: flat/untextured raster {asset.name} "
                        f"(max channel variance {float(np.max(channel_variance)):.2f})"
                    )
    # Fail closed on an incomplete or contaminated raster pack. A generated
    # directory must contain exactly the resources consumed by the game;
    # otherwise an obsolete image can hide a generator regression or inflate
    # the release payload. Ignore no filenames, including hidden leftovers.
    expected_assets = (
        {f"biome_{i:02d}.jpg" for i in range(24)} |
        {f"ore_{i:02d}.png" for i in range(24)} |
        {f"menu_{i}.jpg" for i in range(1, 5)} |
        {"panel.png", "button.png", "button_off.png", "header.png",
         "nav.png", "fractures.png", "miner.png"}
    )
    actual_assets = {item.name for item in assets.iterdir()}
    missing = sorted(expected_assets - actual_assets)
    extra = sorted(actual_assets - expected_assets)
    if missing or extra:
        raise ValueError(
            f"Generated raster manifest mismatch: missing={missing}, extra={extra}"
        )
    if any(not (assets / name).is_file() or (assets / name).is_symlink()
           for name in expected_assets):
        raise ValueError("Raster pack contains a non-file or symlinked asset")
    # Verify all UI skins and menu backdrops, not just the ore/biome subset.
    # The contact-sheet generator checks readability, but explicit image
    # dimensions and alpha rules prevent accidentally publishing empty skins.
    ui_files = ("panel.png", "button.png", "button_off.png", "header.png",
                "nav.png", "fractures.png", "miner.png")
    # Match the dimensions consumed by Java's raster loader and nine-slice.
    # Minimum-size checks alone allow a malformed but decodable PNG to
    # silently change corner seams or make the miner/fracture overlay blurry.
    ui_dimensions = {
        "panel.png": (400, 96),
        "button.png": (160, 64),
        "button_off.png": (160, 64),
        "header.png": (360, 88),
        "nav.png": (360, 50),
        "fractures.png": (300, 300),
        "miner.png": (240, 340),
    }
    menu_dimensions = set()
    for filename in (*ui_files, *(f"menu_{i}.jpg" for i in range(1, 5))):
        path = assets / filename
        with Image.open(path) as img:
            img.load()
            if img.width < 16 or img.height < 16:
                raise ValueError(f"{filename}: undersized interface raster")
            if filename in ui_dimensions and img.size != ui_dimensions[filename]:
                raise ValueError(
                    f"{filename}: expected raster dimensions "
                    f"{ui_dimensions[filename]}, got {img.size}"
                )
            if filename.startswith("menu_") and filename.endswith(".jpg"):
                menu_dimensions.add(img.size)
                # Menu art is authored in the 360x570 logical canvas.
                # A differently sized image can shift focal regions relative
                # to fixed title/navigation coordinates despite matching peers.
                if img.size != (360, 570):
                    raise ValueError(
                        f"{filename}: expected 360x570 logical menu canvas, "
                        f"got {img.size}"
                    )
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
    if len(menu_dimensions) != 1:
        raise ValueError(f"Menu backgrounds have inconsistent dimensions: {sorted(menu_dimensions)}")
    # The enabled and disabled controls must remain distinguishable after
    # alpha compositing onto the actual graphite surface. Different hashes
    # alone do not guarantee visible feedback for a pressed/disabled action.
    import numpy as np
    from PIL import ImageChops
    def composited_button(name):
        with Image.open(assets / name) as source:
            rgba = source.convert("RGBA")
            base = Image.new("RGBA", rgba.size, (19, 27, 36, 255))
            return Image.alpha_composite(base, rgba).convert("RGB")

    enabled = composited_button("button.png")
    disabled = composited_button("button_off.png")
    if enabled.size != disabled.size:
        raise ValueError("button states have mismatched raster dimensions")
    difference = np.asarray(ImageChops.difference(enabled, disabled), dtype=np.uint8)
    changed_fraction = float(np.mean(np.max(difference, axis=2) >= 8))
    mean_difference = float(np.mean(difference))
    if changed_fraction < 0.02 or mean_difference < 1.0:
        raise ValueError(
            "button states are visually indistinguishable on graphite "
            f"(changed={changed_fraction:.2%}, mean delta={mean_difference:.2f})"
        )
    # RGB distance alone can be large for colors that have nearly identical
    # perceived brightness. The disabled state must also remain distinguishable
    # in grayscale (low saturation, color-vision deficiency, screen dimming).
    # Compute sRGB relative luminance after compositing both states on graphite.
    def relative_luminance(rgb):
        srgb = np.asarray(rgb, dtype=np.float32) / 255.0
        linear = np.where(srgb <= 0.04045, srgb / 12.92,
                          ((srgb + 0.055) / 1.055) ** 2.4)
        return (0.2126 * linear[:, :, 0] +
                0.7152 * linear[:, :, 1] +
                0.0722 * linear[:, :, 2])

    luminance_delta = float(np.mean(np.abs(
        relative_luminance(enabled) - relative_luminance(disabled)
    )))
    if luminance_delta < 0.012:
        raise ValueError(
            "button enabled/disabled states have insufficient grayscale "
            f"separation on graphite (mean relative luminance delta "
            f"{luminance_delta:.4f})"
        )
    # Different PNG hashes can still represent the same visible ore (for
    # example, different compression or invisible RGB in transparent pixels).
    # Compare what players actually see after compositing on graphite. The
    # thumbnail check is intentionally conservative: it catches near-clones
    # without requiring different ores to use radically different palettes.
    ore_previews = []
    for i in range(24):
        with Image.open(assets / f"ore_{i:02d}.png") as source:
            rgba = source.convert("RGBA")
            backdrop = Image.new("RGBA", rgba.size, (19, 27, 36, 255))
            visible = Image.alpha_composite(backdrop, rgba).convert("RGB")
            ore_previews.append(np.asarray(
                visible.resize((64, 64), Image.Resampling.BILINEAR),
                dtype=np.float32,
            ))
    ore_distances = []
    for i in range(24):
        for j in range(i + 1, 24):
            difference = float(np.mean(np.abs(ore_previews[i] - ore_previews[j])))
            if not np.isfinite(difference):
                raise ValueError("Non-finite ore similarity metric")
            if difference < 1.5:
                raise ValueError(
                    f"ore_{i:02d}.png and ore_{j:02d}.png are visually "
                    f"indistinguishable on graphite (mean RGB delta "
                    f"{difference:.2f})"
                )
            ore_distances.append({
                "left": f"ore_{i:02d}.png",
                "right": f"ore_{j:02d}.png",
                "mean_rgb_delta": round(difference, 4),
            })
    if len(ore_distances) != 276:
        raise ValueError("Incomplete ore similarity comparisons")
    # Distinct JPEG hashes and nonzero texture variance do not prove that
    # neighboring biomes look different. Detect visually cloned cave scenes,
    # including files re-encoded at different JPEG quality levels. Downsample
    # to remove compression noise and compare decoded RGB, not file bytes.
    biome_previews = []
    for i in range(24):
        with Image.open(assets / f"biome_{i:02d}.jpg") as source:
            biome_previews.append(np.asarray(
                source.convert("RGB").resize(
                    (64, 64), Image.Resampling.BILINEAR
                ), dtype=np.float32,
            ))
    biome_distances = []
    for i in range(24):
        for j in range(i + 1, 24):
            difference = float(np.mean(np.abs(
                biome_previews[i] - biome_previews[j]
            )))
            if not np.isfinite(difference):
                raise ValueError("Non-finite biome similarity metric")
            if difference < 1.5:
                raise ValueError(
                    f"biome_{i:02d}.jpg and biome_{j:02d}.jpg are visually "
                    f"indistinguishable (mean RGB delta {difference:.2f})"
                )
            biome_distances.append({
                "left": f"biome_{i:02d}.jpg",
                "right": f"biome_{j:02d}.jpg",
                "mean_rgb_delta": round(difference, 4),
            })
    if len(biome_distances) != 276:
        raise ValueError("Incomplete biome similarity comparisons")
    # Duplicate menu backgrounds can make distinct navigation destinations
    # look like the same screen, even if all four files decode correctly.
    menu_hashes = [hashlib.sha256((assets / f"menu_{i}.jpg").read_bytes()).digest()
                   for i in range(1, 5)]
    if len(set(menu_hashes)) != 4:
        raise ValueError("duplicate menu backgrounds in four-screen art set")
    # Distinct JPEG byte streams can still encode visually identical backdrops
    # (different compression quality or metadata). Compare decoded, downsampled
    # pixels so every destination has a genuinely distinct visual identity.
    menu_previews = []
    for i in range(1, 5):
        with Image.open(assets / f"menu_{i}.jpg") as img:
            menu_previews.append(np.asarray(
                img.convert("RGB").resize((64, 64), Image.Resampling.BILINEAR),
                dtype=np.float32,
            ))
    # Compute each pair once: use the same decoded-pixel metric for both
    # the acceptance threshold and the review report. This prevents the
    # two checks from silently diverging as the audit evolves.
    menu_distances = []
    for i in range(len(menu_previews)):
        for j in range(i + 1, len(menu_previews)):
            delta = float(np.mean(np.abs(menu_previews[i] - menu_previews[j])))
            if not np.isfinite(delta):
                raise ValueError("Non-finite menu similarity metric")
            if delta < 3.0:
                raise ValueError(
                    f"menu_{i + 1}.jpg and menu_{j + 1}.jpg are visually "
                    f"indistinguishable (mean RGB delta {delta:.2f})"
                )
            menu_distances.append({
                "left": f"menu_{i + 1}.jpg",
                "right": f"menu_{j + 1}.jpg",
                "mean_rgb_delta": round(delta, 4),
            })
    # Every unordered pair of four menu backgrounds must be represented.
    if len(menu_distances) != 6:
        raise ValueError("Incomplete menu similarity comparisons")
    import json
    metrics_path = root / "menu_visual_distances.json"
    metrics_path.write_text(
        json.dumps({"comparisons": menu_distances}, indent=2) + "\n",
        encoding="utf-8",
    )
    if len(menu_distances) != 6 or any(
        not np.isfinite(item["mean_rgb_delta"]) for item in menu_distances
    ):
        raise ValueError("Invalid menu visual distance report")
    # Preserve all 552 pairwise ore/biome distances for independent art review.
    # Keep the existing acceptance thresholds unchanged.
    (root / "world_visual_distances.json").write_text(
        json.dumps({
            "ores": ore_distances,
            "biomes": biome_distances,
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    # Rank the closest-looking assets for focused visual review.
    # This supplements, rather than relaxes, the existing thresholds.
    def closest_pairs(pairs, expected, count):
        if len(pairs) != expected:
            raise ValueError("Incomplete visual comparison set")
        return sorted(
            pairs,
            key=lambda pair: (
                pair["mean_rgb_delta"], pair["left"], pair["right"]
            ),
        )[:count]

    (root / "closest_visual_pairs.json").write_text(
        json.dumps({
            "ores": closest_pairs(ore_distances, 276, 5),
            "biomes": closest_pairs(biome_distances, 276, 5),
            "menus": closest_pairs(menu_distances, 6, 3),
        }, indent=2) + "\n",
        encoding="utf-8",
    )
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
        verify(args.output.expanduser().absolute())



if __name__ == "__main__":
    main()
