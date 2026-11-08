"""Source-only regression for the 24-biome / 24-ore raster contract.

No Android project, Gradle, emulator, GitHub Actions, or asset generation.
Checks generator source via AST so importing it cannot write assets.
"""
import ast
from collections import Counter
from pathlib import Path

SOURCE = Path(__file__).with_name("generate_art_v70.py")
tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
assignments = {
    target.id: node.value
    for node in tree.body if isinstance(node, ast.Assign)
    for target in node.targets if isinstance(target, ast.Name)
}
scenes = ast.literal_eval(assignments["SCENES"])
ores = ast.literal_eval(assignments["ORES"])
if len(scenes) != 24 or len(ores) != 24:
    raise AssertionError("Expected exactly 24 biome and 24 ore palettes")
for name, palette in (("biome", scenes), ("ore", ores)):
    if len(set(palette)) != 24:
        raise AssertionError(f"{name} palettes must be distinct")
    for color in palette:
        if len(color) != 3 or any(type(v) is not int or not 0 <= v <= 255 for v in color):
            raise AssertionError(f"Invalid {name} RGB palette: {color}")

# Validate the expressions used by the generator, not only a duplicated
# mathematical model in this test. This catches a renderer regression where
# the checks below would otherwise keep passing unchanged.
cave_fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "cave")
ore_fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "ore")
assign_signature = [n for n in ast.walk(cave_fn)
                    if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "signature" for t in n.targets)]
if len(assign_signature) != 1:
    raise AssertionError("Expected exactly one geological signature assignment")
expected_signature = ast.parse("index // 4 if index < 24 else (index - 30) % 6", mode="eval").body
if ast.dump(assign_signature[0].value) != ast.dump(expected_signature):
    raise AssertionError("Renderer geological signature formula changed")
ore_conditions = [ast.dump(n.test) for n in ast.walk(ore_fn) if isinstance(n, ast.If)]
for expression in ("index % 3 == 0", "index % 3 == 1"):
    expected = ast.dump(ast.parse(expression, mode="eval").body)
    if expected not in ore_conditions:
        raise AssertionError(f"Ore renderer lost microtexture branch: {expression}")

# Each biome has one of four foreground motifs and one of six signatures.
pairs = [(i % 4, i // 4) for i in range(24)]
if len(set(pairs)) != 24:
    raise AssertionError("Biome foreground/signature combinations collide")
if Counter(m for m, _ in pairs) != {i: 6 for i in range(4)}:
    raise AssertionError("Foreground motif distribution changed")
if Counter(s for _, s in pairs) != {i: 4 for i in range(6)}:
    raise AssertionError("Geological signature distribution changed")
if len({(i - 30) % 6 for i in range(31, 35)}) != 4:
    raise AssertionError("Four menu backdrops share a geological signature")
if Counter(i % 3 for i in range(24)) != {i: 8 for i in range(3)}:
    raise AssertionError("Ore microstructure distribution changed")

calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
def is_call(node, name):
    return isinstance(node.func, ast.Name) and node.func.id == name
if not any(is_call(n, "audit_raster_assets") for n in calls):
    raise AssertionError("Decoded-output raster audit missing")
functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
for required in ("field", "cave", "ore", "panel_art"):
    if required not in functions:
        raise AssertionError(f"Missing renderer: {required}")
print("PASS: 24 unique palettes per category, 24 distinct biome combinations,")
print("      4 menu signatures, 3 balanced ore textures, raster audit wired")
