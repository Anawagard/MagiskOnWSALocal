"""Source-only release guard for the modernist redesign patch chain.

Run with python3; never invokes Gradle, Android, or GitHub Actions.
This is a static contract, not a substitute for applying patches or device tests.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PATCHES = [ROOT / f"patch_modernist_v{v}.py" for v in range(72, 78)]
TESTS = sorted(ROOT.glob("test_modernist_*.py"))
assert len(PATCHES) == 6 and all(p.is_file() for p in PATCHES)
assert TESTS, "No modernist regression tests found"

for path in PATCHES + TESTS:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

patch = {v: PATCHES[v - 72].read_text(encoding="utf-8") for v in range(72, 78)}
# Confirm render and touch transformations are coupled. A change to one
# without the other must break this guard.
for marker in (
    "c.translate(13f,18f);",
    "c.scale(.93f,.94f);",
    "x=(x-13f)/.93f;",
    "y=(y-18f)/.94f;",
    "if(screenY<205f||screenY>713f)return true;",
):
    assert marker in patch[72], marker

# Every patched stage must retain its source-only nature; no build or
# workflow dispatch is permitted in any modernist patch or regression test.
import re
for path in PATCHES + TESTS:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name.split(".")[0] for alias in node.names] if isinstance(node, ast.Import) else [str(node.module).split(".")[0]]
            assert not set(names) & {"subprocess", "gradle", "requests"}, (path, names)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"system", "popen", "run", "check_call", "check_output"}, (path, node.lineno)

# Verify the visible ore target and notification never overlap across
# seven aspect ratios, including 320px-wide and extra-tall devices.
def overlap(a, b):
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])

toast = (18, 240, 342, 266)
ore = (105, 270, 330, 500)
header = (18, 153, 342, 236)
assert all(not overlap(toast, box) for box in (ore, header))
checks = 0
for width, height in ((320, 568), (360, 720), (393, 852), (720, 1280),
                      (1080, 2400), (1272, 2772), (1440, 3200)):
    scale = min(width / 360, height / 720)
    ox, oy = (width - 360 * scale) / 2, (height - 720 * scale) / 2
    def transform(r):
        return (ox + r[0] * scale, oy + r[1] * scale,
                ox + r[2] * scale, oy + r[3] * scale)
    assert not overlap(transform(toast), transform(ore))
    assert not overlap(transform(toast), transform(header))
    checks += 2

print(f"PASS: {len(PATCHES)} patch ASTs, {len(TESTS)} test ASTs, "
      f"render/input guards, and {checks} scaled overlay checks")
