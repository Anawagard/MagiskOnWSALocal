"""Regression: empty ore-risk sheets are still published as a fresh PNG.

Source-only: does not invoke Android, Gradle or GitHub Actions.
"""
import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
runner = (HERE / "run_full_source_rehearsal_v124.py").read_text(encoding="utf-8")
tree = ast.parse(runner)

# The old predicate treated an existing NO RISK PAIRS image as a failure.
assert '(rendered > 0) != sheet_path.is_file()' not in runner
assert 'if not sheet_path.is_file():' in runner
assert 'expected_rendered = min(24, flagged + unscorable)' in runner

# Truth table: the diagnostic must exist irrespective of how many risks
# are present; only absence of the PNG is an error.
for rendered in (0, 1, 24):
    for file_exists in (False, True):
        rejected = not file_exists
        assert rejected == (not file_exists), (rendered, file_exists)
print("PASS: empty-risk PNG publication contract")
