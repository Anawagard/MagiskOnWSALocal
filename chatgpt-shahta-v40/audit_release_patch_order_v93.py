"""Audit the ordered source-patch commands in the manual Android release workflow.

Source-only: reads YAML as text; never executes patches, Gradle or Actions.
This is a dependency/ordering preflight, NOT proof that patches apply.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github/workflows/chatgpt-shahta-v40.yml"
SCRIPT_ROOT = ROOT / "chatgpt-shahta-v40"

# Ordered final visual pipeline: do not silently skip a patch version.
MODERN = ["patch_full_redesign_v70.py"] + [
    f"patch_modernist_v{v}.py" for v in range(71, 80)
]
TESTS = [
    "test_modernist_geometry_v72.py",
    "test_modernist_settings_v73.py",
    "test_modernist_shop_v74.py",
    "test_modernist_hud_v75.py",
    "test_modernist_layout_v76.py",
    "test_modernist_mine_v77.py",
]


def audit(workflow: str, existing: set[str]) -> tuple[list[str], list[str]]:
    # Only full-line commands, not comments or documentation references.
    commands = re.findall(
        r"(?m)^\s*python3\s+chatgpt-shahta-v40/(\w+\.py)\s*$",
        workflow,
    )
    missing = [name for name in MODERN + TESTS if name not in existing]
    missing += [name for name in MODERN + TESTS if commands.count(name) != 1]
    positions = [commands.index(name) for name in MODERN if name in commands]
    if len(positions) != len(MODERN) or positions != sorted(positions):
        missing.append("visual patches absent or out of order")
    if len(set(commands)) != len(commands):
        missing.append("duplicate Python commands")
    return commands, missing


def main() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    # Prevent accidental use as a CI runner on automatic events.
    if not re.search(r"(?m)^  workflow_dispatch:\s*$", workflow):
        raise SystemExit("FAIL: manual dispatch trigger missing")
    if re.search(r"(?m)^  (push|pull_request|schedule|workflow_call):", workflow):
        raise SystemExit("FAIL: unexpected automatic trigger")
    commands, problems = audit(
        workflow, {p.name for p in SCRIPT_ROOT.glob("*.py")}
    )
    if problems:
        raise SystemExit("FAIL: " + "; ".join(problems))
    print(f"PASS: {len(MODERN)} ordered visual patches and "
          f"{len(TESTS)} source-only tests present in manual workflow")
    print("NOTE: integration replay, resource checks and Android validation pending")


if __name__ == "__main__":
    main()
