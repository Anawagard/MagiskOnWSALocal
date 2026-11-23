"""Restore historical Android sources, replay v6.9, then audit v7.9.

Source-only. Never launches Gradle, Android SDK, GitHub Actions or APK builds.
Requires Python, brotli and Pillow. The historical WAV assets are intentionally
not restored, so this rehearsal is NOT a buildable Android release.
Run from any directory: python3 chatgpt-shahta-v40/run_full_source_rehearsal_v124.py
"""
from pathlib import Path
import argparse
import ast
import os
import subprocess
import sys
import tempfile

from audit_archived_baseline_v83 import ARCHIVE
from replay_baseline_source_only import (
    REPO, WORKFLOW, source_steps, verify_replayed_source,
)
from restore_source_only import restore

HERE = Path(__file__).resolve().parent
JAVA = Path("app/src/main/java/com/bezdna/mine/MineView.java")
ACTIVITY = Path("app/src/main/java/com/bezdna/mine/MainActivity.java")



def verify_biome_textures(project):
    """Check actual PNG payloads, not just generator output."""
    import hashlib
    from PIL import Image

    folder = project / "app/src/main/assets/shahta_textures"
    expected = {f"biome_{index:02}.png" for index in range(24)}
    actual = {item.name for item in folder.glob("biome_*.png")}
    if actual != expected:
        raise AssertionError(f"Missing/extra biome textures: {sorted(expected - actual)}, {sorted(actual - expected)}")
    hashes = set()
    for name in sorted(expected):
        path = folder / name
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.format != "PNG" or image.size != (384, 384) or image.mode != "RGB":
                raise AssertionError(f"Unexpected biome texture format: {name}")
        hashes.add(hashlib.sha256(path.read_bytes()).digest())
    if len(hashes) != 24:
        raise AssertionError("Duplicate biome textures detected")
    print("TEXTURES PASS: 24 distinct valid 384x384 RGB PNGs", flush=True)


def verify_modernist_art(project):
    """Fail closed on missing, malformed, duplicate or invisible game art.

    This validates the *generated* files consumed by the Java renderer, not
    fixture stand-ins. It does not invoke Android, Gradle or GitHub Actions.
    """
    import hashlib
    from PIL import Image

    folder = project / "app/src/main/assets/shahta_v70"
    dimensions = {}
    for index in range(24):
        dimensions[f"ore_{index:02}.png"] = ("PNG", (300, 300))
        dimensions[f"biome_{index:02}.jpg"] = ("JPEG", (360, 570))
    for index in range(1, 5):
        dimensions[f"menu_{index}.jpg"] = ("JPEG", (360, 570))
    dimensions.update({
        "fractures.png": ("PNG", (300, 300)),
        "panel.png": ("PNG", (400, 96)),
        "button.png": ("PNG", (160, 64)),
        "button_off.png": ("PNG", (160, 64)),
        "header.png": ("PNG", (360, 88)),
        "nav.png": ("PNG", (360, 50)),
        "miner.png": ("PNG", (240, 340)),
    })
    expected = set(dimensions)
    actual = {item.name for item in folder.iterdir() if item.is_file()}
    missing, unexpected = sorted(expected - actual), sorted(actual - expected)
    if missing or unexpected:
        raise AssertionError(f"Art inventory mismatch: missing={missing}, extra={unexpected}")

    families = {"ore": set(), "biome": set(), "menu": set()}
    for name in sorted(expected):
        path = folder / name
        if path.stat().st_size < 700:
            raise AssertionError(f"Suspiciously small art asset: {name}")
        fmt, size = dimensions[name]
        with Image.open(path) as image:
            image.load()  # Decode actual pixels, not just the file header.
            if image.format != fmt or (size is not None and image.size != size):
                raise AssertionError(
                    f"Invalid raster {name}: {image.format} {image.size}; "
                    f"expected {fmt} {size}")
            if name.startswith("ore_"):
                if image.mode != "RGBA":
                    raise AssertionError(f"Ore must have RGBA transparency: {name}")
                alpha = image.getchannel("A")
                low, high = alpha.getextrema()
                if (low, high) != (0, 255):
                    raise AssertionError(f"Ore silhouette must contain clear and opaque pixels: {name}")
                histogram = alpha.histogram()
                coverage = sum(histogram[128:]) / (image.width * image.height)
                if not 0.15 < coverage < 0.85:
                    raise AssertionError(f"Ore coverage out of bounds: {name} {coverage:.3f}")
            if name.startswith(("biome_", "menu_")) and image.mode != "RGB":
                raise AssertionError(f"Background must be RGB: {name}")
            family = name.split("_", 1)[0]
            if family in families:
                # Compare decoded pixels, so identical art with different
                # compression settings cannot masquerade as distinct biomes.
                # Invisible RGB values under alpha=0 must not make visually
                # identical sprites appear distinct. Compare both black and
                # white mattes to retain transparency and silhouette identity.
                rgba = image.convert("RGBA")
                fingerprint = hashlib.sha256()
                fingerprint.update(repr(image.size).encode("ascii"))
                for matte in ((0, 0, 0, 255), (255, 255, 255, 255)):
                    composite = Image.alpha_composite(
                        Image.new("RGBA", image.size, matte), rgba)
                    fingerprint.update(composite.convert("RGB").tobytes())
                digest = fingerprint.digest()
                if digest in families[family]:
                    raise AssertionError(f"Duplicate decoded raster in {family}: {name}")
                families[family].add(digest)
    if tuple(len(families[k]) for k in ("ore", "biome", "menu")) != (24, 24, 4):
        raise AssertionError("Incomplete raster families")
    print("ART PASS: 59 decoded assets; 24 unique opaque/transparent ores, "
          "24 unique biomes, 4 unique menus, 7 chrome/sprite assets", flush=True)

def rehearse(art_output=None):
    if not __debug__:
        raise SystemExit("BLOCKED: source rehearsal requires assertions; disable -O")
    if os.environ.get("SHAHTA_BASELINE_PROJECT"):
        raise SystemExit("BLOCKED: remove SHAHTA_BASELINE_PROJECT; this runner restores its own baseline")
    # Fail early if any checked-in Python patch, audit or test has invalid syntax.
    # Parse without importing or executing scripts, so this cannot trigger builds.
    scripts = sorted(HERE.glob("*.py"))
    for script in scripts:
        ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
    print(f"PYTHON SOURCE PASS: {len(scripts)} scripts parsed", flush=True)
    # Audit every modernist patch for forbidden build/process/network operations
    # before replaying any historical source. This remains Python-only.
    subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE / "audit_patch_sources.py")],
        cwd=HERE, check=True, timeout=60,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
             "PYTHONUTF8": "1", "PYTHONOPTIMIZE": ""},
    )
    # Keep the latest shop/toast regressions in the canonical source-only gate.
    # These tests inspect the checked-in patch sources and viewport maths only;
    # they must pass before the disposable historical baseline is restored.
    for test in ("test_modernist_workflow_contract_v90.py",
                 "test_manual_trigger_allowlist_v101.py",
                 "test_signing_identity_fail_closed_v130.py",
                 "test_modernist_five_tab_viewports_v103.py",
                 "test_modernist_mine_sprite_touch_v138.py",
                 "test_feature_header_hidden_taps_v139.py",
                 # Active tab identity must match the five contextual toasts.
                 "test_modernist_page_identity_nav_v136.py",
                 "test_modernist_toast_negative_geometry_v137.py",
                 "test_settings_hitboxes_v126.py",
                 "test_viewport_transform_v126.py",
                 "test_affine_source_contract_v127.py",
                 "test_modernist_shop_control_isolation_v128.py",
                 "test_modernist_toast_viewport_v129.py",
                 # Exercise real five-page toast and header suppression contracts.
                 "test_modernist_context_toast_v106.py",
                 "test_modernist_layout_v76.py",
                 "test_modernist_notification_geometry_v109.py",
                 # Pixel-level raster regressions must run, not merely parse.
                 "test_ore_biome_displayed_contrast_source_only.py",
                 "test_ore_visibility_pixels_source_only.py",
                 "test_heatmap_metric_integrity_source_only.py",
                 "test_core_mean_bound_source_only.py",
                 "test_ore_visibility_details_source_only.py",
                 "test_ore_raster_inputs_source_only.py",
                 # Compare the actual 24 rendered lodes against pre-lode rasters.
                 "test_ore_macro_lodes_source_only_v131.py",
                 # Confirm corners remain pixel-perfect after nine-slice scaling.
                 "test_raster_chrome_nineslice_corners_v132.py",
                 "test_ui_asset_dimensions_source_only_v133.py",
                 "test_ore_core_visibility_source_only.py",
                 "test_alpha_sensitivity_source_only.py",
                 "test_alpha_sensitivity_matrix_source_only.py",
                 "test_ore_visibility_risk_summary_source_only.py",
                 "test_ore_risk_threshold_types_source_only.py",
                 "test_diagnostic_output_isolation_source_only_v135.py",
                 "test_diagnostic_path_collision_source_only.py",
                 "test_ore_matrix_completeness_v135.py",
                 # Exercise the complete 24x24 fixture and malformed raster inputs.
                 "test_art_occupancy_assignment_v133.py",
                 "test_ore_matrix_integration_source_only.py",
                 "test_ore_visibility_heatmap_v134.py",
                 "test_rehearsal_heatmap_integration_source_only.py",
                 "test_visibility_json_atomic_source_only.py",
                 # Verify the contrast sampler tracks the actual Java ore position.
                 "test_ore_backdrop_registration_v133.py",
                 # Audit all 576 displayed ore/biome pairs and the atlas publisher.
                 "test_all_ore_biome_atlas_source_only.py",
                 "test_render_art_contact_sheet_source_only.py",
                 "test_risk_sheet_atomic_source_only.py",
                 "test_risk_sheet_output_safety_source_only.py",
                 "test_risk_sheet_symlink_guard_source_only.py"):
        subprocess.run(
            [sys.executable, "-X", "utf8", str(HERE / test)],
            # Raster-diff of 24 ores renders 48 images; a 60-second cap can
            # falsely fail on slow machines despite no correctness issue.
            cwd=HERE, check=True, timeout=180 if "macro_lodes" in test else 60,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                 "PYTHONUTF8": "1", "PYTHONOPTIMIZE": ""},
        )
    # Validate the complete standalone raster pipeline before historical replay.
    # This exercises the actual 48 generated images, pixel diversity, opacity,
    # button-state contrast and contact sheets, rather than source signatures.
    # All output is disposable; no Gradle, APK or GitHub Actions are invoked.
    art_command = [sys.executable, "-X", "utf8",
                   str(HERE / "verify_generated_art_source_only.py")]
    if art_output is not None:
        art_command.extend(("--output", str(art_output)))
    subprocess.run(
        art_command,
        cwd=HERE, check=True, timeout=300,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
             "PYTHONUTF8": "1", "PYTHONOPTIMIZE": ""},
    )
    print("RASTER SOURCE-ONLY PASS: 48 assets and contact sheets", flush=True)
    steps = source_steps(WORKFLOW.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="shahta-full-source-") as folder:
        root = Path(folder)
        project = root / "chatgpt-shahta-v33/project"
        count = restore(ARCHIVE, project)
        initial_activity = (project / ACTIVITY).read_bytes()
        for index, relative in enumerate(steps, 1):
            print(f"BASELINE {index}/{len(steps)} {relative}", flush=True)
            subprocess.run(
                [sys.executable, "-X", "utf8", str(REPO / relative)],
                cwd=root, check=True, timeout=180,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1",
                     "PYTHONOPTIMIZE": ""},
            )
        verify_replayed_source(root, initial_activity)
        verify_biome_textures(project)
        # The modernist patches reference raster sprites generated by a separate
        # workflow step. Generate them inside the disposable tree, not checkout.
        # The art generator defaults to repository sources for release builds;
        # SHAHTA_ART_PROJECT redirects only this source-only rehearsal.
        subprocess.run(
            [sys.executable, "-X", "utf8", str(HERE / "generate_art_v70.py")],
            cwd=root, check=True, timeout=300,
            env={**os.environ, "SHAHTA_ART_PROJECT": str(project),
                 "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1",
                     "PYTHONOPTIMIZE": ""},
        )
        verify_modernist_art(project)
        # Run the full visual-asset contract against the actual generated files.
        # The lightweight check above only validates presence and PNG/JPEG headers;
        # this also rejects duplicate ores/biomes, flat sprites, bad transparency,
        # incorrect dimensions and visually indistinguishable button states.
        from audit_raster_assets_v710 import audit as audit_raster_identity
        audit_raster_identity(project / "app/src/main/assets/shahta_v70")
        # Measure decoded pixels of every biome/ore combination, not just
        # file headers or palette constants. Fail on missing/non-finite scores.
        import math
        from audit_ore_biome_composites_source_only import analyze
        scores = analyze(project / "app/src/main/assets/shahta_v70")
        if len(scores) != 24 * 24:
            raise AssertionError(f"Expected 576 biome/ore pairs, got {len(scores)}")
        pairs = {(row["biome"], row["ore"]) for row in scores}
        if pairs != {(i, j) for i in range(1, 25) for j in range(1, 25)}:
            raise AssertionError("Incomplete or duplicated biome/ore contrast matrix")
        for row in scores:
            if not all(math.isfinite(row[key]) and 0 <= row[key] <= 1
                       for key in ("score", "visible_coverage", "weakest_decile", "core_coverage")):
                raise AssertionError(f"Invalid raster contrast measurement: {row}")
            core_mean = row["core_mean_contrast"]
            if core_mean is not None and not (math.isfinite(core_mean) and 0 <= core_mean <= 1):
                raise AssertionError(f"Invalid mean ore core contrast: {row}")
            if (row["core_coverage"] == 0) != (core_mean is None):
                raise AssertionError(f"Core mean/coverage mismatch: {row}")
            core_score = row["core_weakest_decile"]
            if core_score is not None and not (math.isfinite(core_score) and 0 <= core_score <= 1):
                raise AssertionError(f"Invalid ore core contrast measurement: {row}")
            fraction = row["core_low_contrast_fraction"]
            if fraction is not None and not (math.isfinite(fraction) and 0 <= fraction <= 1):
                raise AssertionError(f"Invalid low-contrast core fraction: {row}")
            if (row["core_coverage"] == 0) != (fraction is None):
                raise AssertionError(f"Core fraction/coverage mismatch: {row}")
            if (row["core_coverage"] == 0) != (core_score is None):
                raise AssertionError(f"Core weakest-decile/coverage mismatch: {row}")
        # Turn pixel diagnostics into a reproducible, per-biome review queue.
        # Counts must account for every flagged pair exactly once.
        from audit_ore_biome_composites_source_only import summarize_risks, render_risk_contact_sheet
        risks = summarize_risks(scores, require_complete=True)
        flagged = risks["risk_pairs"]
        if (sum(risks["risk_count_by_biome"].values()) != flagged
                or sum(risks["risk_count_by_ore"].values()) != flagged
                or len(risks["worst_pairs"]) != flagged):
            raise AssertionError("Inconsistent raster visibility risk counts")
        unscorable = risks["unscorable_core_pairs"]
        locations = risks["unscorable_core_locations"]
        if (unscorable != len(locations)
                or unscorable + flagged > len(scores)
                or len({(r["biome"], r["ore"]) for r in locations}) != unscorable
                or any((r["biome"], r["ore"]) not in pairs for r in locations)):
            raise AssertionError("Inconsistent unscorable ore-core accounting")
        # Persist the full deterministic 576-pair matrix when a review folder
        # was explicitly requested. The console top-ten is not enough to fix
        # every problematic ore/biome combination in a later art pass.
        if art_output is not None:
            import json
            output_dir = Path(art_output)
            output_dir.mkdir(parents=True, exist_ok=True)
            report_path = output_dir / "ore_biome_visibility_576.json"
            report = {"pair_count": len(scores), "scores": scores,
                      "visibility_risks": risks}
            # Publish JSON atomically: a failed serialization or interrupted
            # write must not truncate a previously valid 576-pair report.
            # Use a sibling file so os.replace stays on the same filesystem.
            report_tmp = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", prefix=".shahta-visibility-",
                    suffix=".json", dir=output_dir, delete=False,
                ) as handle:
                    report_tmp = Path(handle.name)
                    json.dump(report, handle, ensure_ascii=False,
                              indent=2, allow_nan=False)
                    handle.write("\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(report_tmp, report_path)
            finally:
                if report_tmp is not None:
                    report_tmp.unlink(missing_ok=True)
            # Publish the complete 24x24 visibility heatmap alongside JSON.
            # Validate metrics before writing either diagnostic image.
            from audit_ore_biome_composites_source_only import render_visibility_heatmap
            heatmap_path = output_dir / "ore_biome_visibility_heatmap.png"
            render_visibility_heatmap(
                scores, heatmap_path,
                assets=project / "app/src/main/assets/shahta_v70",
            )
            if not heatmap_path.is_file():
                raise AssertionError("Visibility heatmap PNG was not published")
            print(f"RASTER VISIBILITY HEATMAP: {heatmap_path}", flush=True)
            # Generate the real 576-pair review contact sheet, not only JSON.
            # Keep both unscorable cores and low-contrast combinations visible.
            sheet_path = output_dir / "ore_biome_risks.png"
            rendered = render_risk_contact_sheet(
                project / "app/src/main/assets/shahta_v70", scores, sheet_path,
                limit=24,
            )
            expected_rendered = min(24, flagged + unscorable)
            if rendered != expected_rendered:
                raise AssertionError(
                    f"Risk contact sheet has {rendered} tiles, expected {expected_rendered}"
                )
            # The renderer deliberately publishes a current NO RISK PAIRS PNG
            # even when there are zero flagged combinations. A missing file
            # is always a failure; zero selected tiles is not.
            if not sheet_path.is_file():
                raise AssertionError("Risk contact sheet PNG was not published")
            print(f"RASTER REVIEW REPORT: {report_path}", flush=True)
            print(f"RASTER RISK SHEET: {sheet_path} ({rendered} tiles)", flush=True)
            # Publish the complete visual matrix for human review, including
            # combinations that pass numeric risk thresholds. This is generated
            # only when an explicit diagnostic output directory was requested.
            from preview_all_ore_biome_pairs_source_only import render_atlas
            atlas_path = output_dir / "ore_biome_all_576.png"
            render_atlas(project / "app/src/main/assets/shahta_v70",
                         atlas_path, tile=48)
            from PIL import Image
            with Image.open(atlas_path) as atlas:
                atlas.load()
                if atlas.format != "PNG" or atlas.size != (1255, 1255):
                    raise AssertionError("Complete 576-pair review atlas has invalid dimensions")
            print(f"RASTER FULL ATLAS: {atlas_path} (576 pairs)", flush=True)
        print(f"RASTER CORE COVERAGE REVIEW: {unscorable}/576 pairs lack a scorable opaque core", flush=True)
        print(f"RASTER VISIBILITY REVIEW: {flagged}/576 pairs have >=25% "
              f"low-contrast ore core; worst 10: "
              f"{[(r['biome'], r['ore']) for r in risks['worst_pairs'][:10]]}",
              flush=True)
        print(f"PIXEL CONTRAST PASS: {len(scores)} decoded biome/ore pairs; "
              f"lowest={scores[0]['score']:.6f}", flush=True)
        print(f"BASELINE PASS: {count} archived files, {len(steps)} v6.9 source steps", flush=True)
        subprocess.run(
            [sys.executable, str(HERE / "verify_modernist_patch_chain.py")],
            cwd=root, check=True, timeout=300,
            env={**os.environ, "SHAHTA_BASELINE_PROJECT": str(project),
                 "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1",
                     "PYTHONOPTIMIZE": ""},
        )
        print("PASS: restored v6.9 and applied modernist source-only chain; no APK", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--art-output", type=Path,
                        help="Keep generated PNG/JPEG sprites, JSON audit and contact sheets "
                             "in a new or empty directory for manual review")
    args = parser.parse_args()
    rehearse(args.art_output.expanduser().resolve() if args.art_output else None)
