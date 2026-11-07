"""Source-only regression for manual-only workflow trigger auditing."""
from pathlib import Path
import ast

SOURCE = Path(__file__).with_name("audit_archived_baseline_v83.py")
WORKFLOW = SOURCE.parent.parent / ".github/workflows/chatgpt-shahta-v40.yml"

def events_in(text):
    lines = text.splitlines()
    roots = [i for i, line in enumerate(lines)
             if line.strip() in ("on:", "'on':", '"on":') and line == line.lstrip()]
    if len(roots) != 1:
        raise AssertionError("Expected one root on: mapping")
    events = []
    for line in lines[roots[0] + 1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace():
            break
        if line.startswith("  ") and not line.startswith("    "):
            events.append(line.strip().split(":", 1)[0].strip("'\""))
    return events

def main():
    ast.parse(SOURCE.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert events_in(workflow) == ["workflow_dispatch"]
    for extra in ("issues:", "release:", "repository_dispatch:", "workflow_run:"):
        candidate = workflow.replace("  workflow_dispatch:", "  workflow_dispatch:\n  " + extra, 1)
        assert events_in(candidate) != ["workflow_dispatch"], extra
    print("PASS: manual-only event allowlist source regression; no Android build")

if __name__ == "__main__":
    main()
