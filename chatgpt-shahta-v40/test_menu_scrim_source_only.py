"""Source-only regression: menu scrim must be executable and darken the title band.

Run: python test_menu_scrim_source_only.py
No Android SDK, Pillow, or NumPy required.
"""
import ast
import math
from pathlib import Path

SOURCE = Path(__file__).with_name("generate_art_v70.py")


def test_scrim_assignment():
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SOURCE))
    assignments = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name) and target.id == "vertical"
    ]
    assert len(assignments) == 1, "menu vertical fade must be an executable assignment"
    cave = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "cave")
    guards = [n for n in ast.walk(cave) if isinstance(n, ast.If)
              and ast.unparse(n.test) == "31 <= index <= 34"]
    assert len(guards) == 1, "scrim must affect only the four menu backgrounds"
    guard = guards[0]
    assert assignments[0] in list(ast.walk(guard)), "fade must execute inside menu guard"
    expressions = {t.id: ast.unparse(n.value)
                   for n in ast.walk(guard) if isinstance(n, ast.Assign)
                   for t in n.targets if isinstance(t, ast.Name)}
    assert expressions["vertical"] == "0.55 + 0.45 * np.clip((yy - h * 0.04) / (h * 0.24), 0, 1)"
    assert expressions["center"] == "np.exp(-((xx - w * 0.5) / (w * 0.34)) ** 4)"
    assert expressions["scrim"] == "(0.18 + 0.42 * center * vertical)[:, :, None]"
    assert expressions["rgb"] == "rgb * (1 - scrim) + graphite[None, None, :] * scrim"
    assert not any("\\n        vertical=" in line for line in source.splitlines()), (
        "escaped newline must not comment out the fade"
    )


def test_scrim_bounds():
    # Independent scalar evaluation of the generator's documented formula.
    for width, height in ((360, 570), (240, 360), (1080, 1920)):
        values = []
        for y in (0, height * .04, height * .16, height * .28, height):
            vertical = .55 + .45 * max(0, min(1, (y - height * .04) / (height * .24)))
            center = math.exp(-((width * .5 - width * .5) / (width * .34)) ** 4)
            scrim = .18 + .42 * center * vertical
            assert .18 <= scrim <= .60 + 1e-12
            values.append(scrim)
        assert values[0] < values[2] < values[3]
        assert abs(values[3] - values[4]) < 1e-12


if __name__ == "__main__":
    test_scrim_assignment()
    test_scrim_bounds()
    print("PASS: menu scrim AST and portrait-size math (source-only)")
