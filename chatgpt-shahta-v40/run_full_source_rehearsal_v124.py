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
    """Validate the raster sprites actually loaded by v7.0 Java screens."""
    from PIL import Image
    folder = project / "app/src/main/assets/shahta_v70"
    expected = ({f"ore_{i:02}.png" for i in range(24)} |
                {f"biome_{i:02}.jpg" for i in range(24)} |
                {f"menu_{i}.jpg" for i in range(1, 5)} |
                {"fractures.png", "panel.png", "button.png",
                 "button_off.png", "header.png", "nav.png", "miner.png"})
    missing = sorted(name for name in expected if not (folder / name).is_file())
    if missing:
        raise AssertionError(f"Missing v7.0 art assets: {missing}")
    for name in sorted(expected):
        path = folder / name
        if path.stat().st_size < 700:
            raise AssertionError(f"Suspiciously small art asset: {name}")
        with Image.open(path) as img:
            img.verify()
    print(f"ART PASS: {len(expected)} decoded raster assets, including 24 ore sprites", flush=True)

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
                 "test_settings_hitboxes_v126.py",
                 "test_viewport_transform_v126.py",
                 "test_affine_source_contract_v127.py",
                 "test_modernist_shop_control_isolation_v128.py",
                 "test_modernist_toast_viewport_v129.py",
                 # Pixel-level raster regressions must run, not merely parse.
                 "test_ore_biome_displayed_contrast_source_only.py",
                 "test_ore_visibility_pixels_source_only.py",
                 "test_ore_visibility_details_source_only.py",
                 "test_ore_raster_inputs_source_only.py",
                 "test_ore_core_visibility_source_only.py",
                 "test_alpha_sensitivity_source_only.py",
                 "test_alpha_sensitivity_matrix_source_only.py",
                 "test_ore_visibility_risk_summary_source_only.py",
                 # Exercise the complete 24x24 fixture and malformed raster inputs.
                 "test_ore_matrix_integration_source_only.py"):
        subprocess.run(
            [sys.executable, "-X", "utf8", str(HERE / test)],
            cwd=HERE, check=True, timeout=60,
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
            core_score = row["core_weakest_decile"]
            if core_score is not None and not (math.isfinite(core_score) and 0 <= core_score <= 1):
                raise AssertionError(f"Invalid ore core contrast measurement: {row}")
            fraction = row["core_low_contrast_fraction"]
            if fraction is not None and not (math.isfinite(fraction) and 0 <= fraction <= 1):
                raise AssertionError(f"Invalid low-contrast core fraction: {row}")
            if (row["core_coverage"] == 0) != (fraction is None):
                raise AssertionError(f"Core fraction/coverage mismatch: {row}")
            if row["core_coverage"] == 0 and core_score is not None:
                raise AssertionError(f"Empty ore core must have no score: {row}")
        # Turn pixel diagnostics into a reproducible, per-biome review queue.
        # Counts must account for every flagged pair exactly once.
        from audit_ore_biome_composites_source_only import summarize_risks
        risks = summarize_risks(scores)
        flagged = risks["risk_pairs"]
        if (sum(risks["risk_count_by_biome"].values()) != flagged
                or sum(risks["risk_count_by_ore"].values()) != flagged
                or len(risks["worst_pairs"]) != flagged):
            raise AssertionError("Inconsistent raster visibility risk counts")
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
            report_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\\n",
                encoding="utf-8",
            )
            print(f"RASTER REVIEW REPORT: {report_path}", flush=True)
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
