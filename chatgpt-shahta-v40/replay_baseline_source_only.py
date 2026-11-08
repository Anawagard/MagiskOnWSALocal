"""Reconstruct a disposable v6.9 Android source baseline without Gradle or Actions.

Run: python3 chatgpt-shahta-v40/replay_baseline_source_only.py
Requires brotli and Pillow (for the v6.9 raster generator). Does not fetch
audio, create an APK, invoke Android tools or modify the repository checkout.
The v3.7 WAV recordings are intentionally absent: this is a SOURCE rehearsal,
not a buildable release. Never use its output for a signed APK.
"""
import ast
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from restore_source_only import restore
from audit_archived_baseline_v83 import ARCHIVE

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
WORKFLOW = REPO / ".github/workflows/chatgpt-shahta-v40.yml"
JAVA = Path("chatgpt-shahta-v33/project/app/src/main/java/com/bezdna/mine/MineView.java")
GRADLE = Path("chatgpt-shahta-v33/project/app/build.gradle")
# Read actual release order, rather than maintaining a second patch list.
PATCH_COMMAND = re.compile(r"^\s*(?:run:\s*)?python3\s+(chatgpt-shahta-[\w-]+/(?:patch_[\w]+|generate_raster_v69)\.py)\s*$")

def source_steps(workflow):
    commands = []
    for line in workflow.splitlines():
        match = PATCH_COMMAND.match(line)
        if match:
            path = match.group(1)
            commands.append(path)
            if path.endswith("/patch_raster_v69.py"):
                break
    else:
        raise ValueError("Release workflow lacks the v6.9 terminal patch")
    if not commands or not commands[0].endswith("/patch_game.py"):
        raise ValueError("Release workflow patch order has changed")
    if len(commands) != len(set(commands)):
        raise ValueError("Duplicate release patch step")
    if not any(p.endswith("/patch_real_audio.py") for p in commands):
        raise ValueError("Missing v3.7 source audio patch")
    generator = "chatgpt-shahta-v40/generate_raster_v69.py"
    terminal = "chatgpt-shahta-v40/patch_raster_v69.py"
    if generator not in commands:
        raise ValueError("Missing v6.9 raster generator")
    if commands[-2:] != [generator, terminal]:
        raise ValueError("v6.9 raster generator must immediately precede terminal patch")
    for relative in commands:
        script = REPO / relative
        if not script.is_file():
            raise FileNotFoundError(script)
        ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
    return commands

def verify_replayed_source(root, initial):
    """Check restored release identity, persistence and signing without Gradle."""
    project = root / "chatgpt-shahta-v33/project"
    gradle = (root / GRADLE).read_text(encoding="utf-8")
    source = (root / JAVA).read_text(encoding="utf-8")
    if not re.search(r"(?m)^\s*versionCode\s+46\s*$", gradle) or not re.search(
        r"""(?m)^\s*versionName\s+['"]6\.9['"]\s*$""", gradle
    ):
        raise AssertionError("Replayed project is not v6.9")
    for marker in ("public void save()", "private void rebirth()",
                   'getSharedPreferences("mine_save_v1"'):
        if marker not in source:
            raise AssertionError(f"Missing game-state contract: {marker}")
    if "signingConfig signingConfigs.shahtaDebug" not in gradle:
        raise AssertionError("Pinned debug signing missing")
    if (project / "app/src/main/java/com/bezdna/mine/MainActivity.java").read_bytes() == initial:
        raise AssertionError("Expected historical save import/export updates missing")

def main():
    if not __debug__:
        raise SystemExit("BLOCKED: run without Python -O")
    steps = source_steps(WORKFLOW.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="shahta-v69-source-") as directory:
        root = Path(directory)
        project = root / "chatgpt-shahta-v33/project"
        count = restore(ARCHIVE, project)
        initial = (project / "app/src/main/java/com/bezdna/mine/MainActivity.java").read_bytes()
        # Patch scripts use relative paths, so run in the disposable tree.
        # The original scripts live outside it and are never modified.
        for index, relative in enumerate(steps, 1):
            print(f"SOURCE {index}/{len(steps)} {relative}", flush=True)
            subprocess.run([sys.executable, str(REPO / relative)], cwd=root,
                           check=True, timeout=180, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        verify_replayed_source(root, initial)
        print(f"PASS: {count} archived files, {len(steps)} source-only steps, v6.9 "
              "and persistence/signing markers; disposable tree removed; no APK")
        print("NOTE: WAV audio files are absent; this is not a buildable release.")

if __name__ == "__main__":
    main()
