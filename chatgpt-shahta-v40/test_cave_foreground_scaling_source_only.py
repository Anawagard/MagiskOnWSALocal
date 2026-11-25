"""Source-only regression: foreground cave shelves stay within side walls."""
import ast
from pathlib import Path

source = Path(__file__).with_name("generate_art_v70.py").read_text(encoding="utf-8")
tree = ast.parse(source)
cave = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "cave")
snippet = ast.get_source_segment(source, cave)
for marker in (
    "motif_sx, motif_sy = w / 360.0, h / 570.0",
    "motif_wall = max(1, min(70, w // 5))",
    "reach=min(motif_wall-1",
    "span=min(motif_wall-1",
    "upper=max(0,",
    "lower=min(h-1,",
):
    assert marker in snippet, f"Missing foreground scaling contract: {marker}"

checks = 0
for w, h in ((240, 360), (360, 570), (1080, 1920), (1272, 2772)):
    sx, sy = w / 360.0, h / 570.0
    wall = max(1, min(70, w // 5))
    for j in range(9):
        for jitter in (-12, 12):
            y = round((85 + j * 43 + jitter) * sy)
            for extent in (17, 53):
                reach = min(wall - 1, max(1, round(extent * sx)))
                upper = max(0, y - round(18 * sy))
                lower = min(h - 1, y + round(23 * sy))
                assert 0 <= upper <= y <= lower < h
                assert 0 <= reach < wall
                checks += 2
    for j in range(12):
        for jitter in (-9, 9):
            y = round((65 + j * 39 + jitter) * sy)
            for extent in (34, 70):
                span = min(wall - 1, max(1, round(extent * sx)))
                assert 0 <= y < h
                assert 0 <= span < wall
                assert 0 <= min(h - 1, y + round(11 * sy)) < h
                checks += 3
print(f"Cave foreground scaling: PASS ({checks} extrema checks)")
