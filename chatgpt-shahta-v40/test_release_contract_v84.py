"""Validate the manual-only release contract without running Android or Gradle.

Usage: python3 chatgpt-shahta-v40/test_release_contract_v84.py
This checks the actual release workflow, not a claimed APK version.
"""
from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parent.parent
FLOW = ROOT / ".github/workflows/chatgpt-shahta-v40.yml"
SCRIPTS = ROOT / "chatgpt-shahta-v40"


def audit():
    data = FLOW.read_text(encoding="utf-8")
    assert re.search(r"(?m)^on:\s*\n  workflow_dispatch:\s*$", data), "Game workflow must be manual-only"
    assert not re.search(r"(?m)^  (push|pull_request|schedule|workflow_run):", data), "Unexpected automatic trigger"
    assert data.count("gradle :app:assembleDebug") == 1, "Expected exactly one release APK build"
    assert "actions/upload-artifact@v4" in data, "APK artifact upload missing"
    assert "android_smoke_v70.sh" in data, "Android smoke gate missing"

    scripts = [f"patch_modernist_v{i}.py" for i in range(71, 78)]
    offsets = []
    for name in scripts:
        pattern = rf"(?m)^\s*python3 chatgpt-shahta-v40/{re.escape(name)}\s*$"
        found = list(re.finditer(pattern, data))
        assert len(found) == 1, f"Patch absent or duplicated: {name}"
        offsets.append(found[0].start())
        path = SCRIPTS / name
        assert path.is_file(), f"Missing patch file: {name}"
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assert offsets == sorted(offsets), "Modernist patches are out of order"
    assert offsets[-1] < data.index("gradle :app:assembleDebug"), "Build precedes source patches"
    assert "patch_full_redesign_v70.py" in data, "Missing v7.0 source preparation"

    # Never silently label an older or unverified binary as a newer release.
    match = re.search(r"artifacts/(Shahta-Bez-Dna-v[\d.]+\.apk)", data)
    assert match, "No named APK artifact found"
    apk_name = match.group(1)
    version = re.search(r"v([\d.]+)\.apk$", apk_name).group(1)
    assert f"versionName '{version}'" in data or version == "7.0.1", (
        "APK filename does not match a declared release version"
    )
    print("PASS: manual-only workflow; one build; ordered v7.1-v7.7 patch chain; smoke gate")
    print(f"WARNING: release output is named {apk_name}; this test does NOT verify Gradle version or binary contents.")
    print("NOTE: passing this audit does not prove patches apply or Android compilation succeeds.")


if __name__ == "__main__":
    audit()
