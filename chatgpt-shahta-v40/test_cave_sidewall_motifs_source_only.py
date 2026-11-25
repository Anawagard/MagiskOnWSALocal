"""Source-only regression for scaled cave nodule and fracture motifs."""
import ast
from pathlib import Path

source = Path(__file__).with_name("generate_art_v70.py").read_text(encoding="utf-8")
tree = ast.parse(source)
cave = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "cave")
snippet = ast.get_source_segment(source, cave)
for marker in ("base_x*sx", "int(r.integers(80,480))*sy",
               "int(r.integers(70,510))*sy", "round(17*sy)",
               "round(31*sy)", "max(1,round(3*min(sx,sy)))"):
    assert marker in snippet, f"Missing scaled motif contract: {marker}"

# Exercise extrema, not random samples, across narrow and large viewports.
for w, h in ((240,360), (360,570), (1080,1920), (1272,2772)):
    sx, sy = w/360.0, h/570.0
    for x in (15, 59, 300, 344):
        for y in (80, 479):
            for radius in (4, 14):
                px, py = round(x*sx), round(y*sy)
                r = max(1,round(radius*min(sx,sy)))
                assert 0 <= px-r and px+r < w
                assert 0 <= py-r and py+r < h
    for x in (16,58,301,343):
        for y in (70,509):
            px, py = round(x*sx), round(y*sy)
            for vx, vy in ((px,py),(px+round(8*sx),py+round(17*sy)),
                           (px-round(2*sx),py+round(31*sy))):
                assert 0 <= vx < w and 0 <= vy < h
print("Cave sidewall motif scaling: PASS (4 viewports, extrema)")
