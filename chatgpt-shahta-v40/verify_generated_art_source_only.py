"""Run the real 48-image art pipeline without restoring Android or building an APK.

Usage: python verify_generated_art_source_only.py
Requires Pillow and numpy. Uses temporary directories only; does not touch
Android project files, workflows, signing keys, or game saves.
"""
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


def main():
    with tempfile.TemporaryDirectory(prefix="shahta-real-art-") as tmp:
        root = Path(tmp)
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
        assert len(data["biomes"]) == len(data["ores"]) == 24
        for name in ("biomes", "ores"):
            entries = data[name]
            assert len({item["sha256"] for item in entries}) == 24
            neighbors = data[f"{name}_nearest_neighbors"]
            assert len(neighbors) == 24
            assert all(item["nearest_file"] != item["file"] for item in neighbors)
        for group in ("biomes", "ores", "interface"):
            path = sheets / f"shahta_{group}_contact_sheet.png"
            with Image.open(path) as img:
                img.verify()
        print("PASS: 24 generated biomes, 24 generated ores, diversity audit, "
              "and 3 real contact sheets (source-only; no Android build)")


if __name__ == "__main__":
    main()
