"""Restore historical Android sources, replay v6.9, then audit v7.9.

Source-only. Never launches Gradle, Android SDK, GitHub Actions or APK builds.
Requires Python, brotli and Pillow. The historical WAV assets are intentionally
not restored, so this rehearsal is NOT a buildable Android release.
Run from any directory: python3 chatgpt-shahta-v40/run_full_source_rehearsal_v124.py
"""
from pathlib import Path
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

def rehearse():
    if not __debug__:
        raise SystemExit("BLOCKED: source rehearsal requires assertions; disable -O")
    if os.environ.get("SHAHTA_BASELINE_PROJECT"):
        raise SystemExit("BLOCKED: remove SHAHTA_BASELINE_PROJECT; this runner restores its own baseline")
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
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"},
            )
        verify_replayed_source(root, initial_activity)
        verify_biome_textures(project)
        print(f"BASELINE PASS: {count} archived files, {len(steps)} v6.9 source steps", flush=True)
        subprocess.run(
            [sys.executable, str(HERE / "verify_modernist_patch_chain.py")],
            cwd=root, check=True, timeout=300,
            env={**os.environ, "SHAHTA_BASELINE_PROJECT": str(project),
                 "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"},
        )
        print("PASS: restored v6.9 and applied modernist source-only chain; no APK", flush=True)


if __name__ == "__main__":
    rehearse()
