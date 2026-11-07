"""Source-only release gate: prevent accidental intermediate Android builds.

Checks the game's dedicated workflow only. Never invokes Gradle or Actions.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github/workflows/chatgpt-shahta-v40.yml"
PATCH_DIR = ROOT / "chatgpt-shahta-v40"


def audit(text: str) -> None:
    # A manual-only workflow must not run on pushes, pull requests, schedules,
    # or workflow chaining. YAML's 'on' is intentionally inspected as text to
    # avoid YAML 1.1 parsers silently interpreting it as boolean True.
    # Reject duplicate top-level event mappings: YAML parsers may silently
    # accept the last one, bypassing the manual-only release gate.
    event_keys = re.findall(r"(?m)^on\s*:", text)
    assert len(event_keys) == 1, f"Expected exactly one on: mapping, got {len(event_keys)}"
    match = re.search(r"(?m)^on:[ \t]*(?:\r?\n)", text)
    assert match, "Missing explicit top-level on: mapping"
    tail = text[match.end():]
    block = re.split(r"(?m)^[^\s#][^\n]*:\s*(?:\r?\n|$)", tail, maxsplit=1)[0]
    triggers = re.findall(r"(?m)^  ([a-zA-Z_][\w-]*):", block)
    assert triggers == ["workflow_dispatch"], f"Non-manual triggers: {triggers}"
    for version in range(70, 80):
        name = ("patch_full_redesign_v70.py" if version == 70 else
                f"patch_modernist_v{version}.py")
        assert (PATCH_DIR / name).is_file(), f"Missing patch {name}"
    chain = ["patch_full_redesign_v70.py"] + [
        f"patch_modernist_v{version}.py" for version in range(71, 80)
    ]
    positions = []
    for name in chain:
        occurrences = [m.start() for m in re.finditer(re.escape(name), text)]
        assert len(occurrences) == 1, f"Patch reference missing or duplicated: {name}"
        positions.append(occurrences[0])
    assert positions == sorted(positions), "Patch order differs from release chain"


def test_negative_cases(text: str) -> None:
    duplicate = text + "\non:\n  push:\n"
    try:
        audit(duplicate)
    except AssertionError:
        pass
    else:
        raise AssertionError("Duplicate top-level on: mapping not rejected")
    for trigger in ("push", "pull_request", "schedule", "workflow_run"):
        injected = text.replace("  workflow_dispatch:", f"  {trigger}:\n  workflow_dispatch:", 1)
        try:
            audit(injected)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"Unsafe trigger not rejected: {trigger}")


if __name__ == "__main__":
    source = WORKFLOW.read_text(encoding="utf-8")
    audit(source)
    test_negative_cases(source)
    print("PASS: v7.0-v7.9 ordered and game workflow remains manual-only; no build")
