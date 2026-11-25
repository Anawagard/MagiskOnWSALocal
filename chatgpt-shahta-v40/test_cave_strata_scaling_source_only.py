"""Regression: lithology bands and fault branches scale with raster dimensions.

No Android build, assets, or external dependencies required.
"""
import ast
from pathlib import Path

source = Path(__file__).with_name("generate_art_v70.py").read_text(encoding="utf-8")
tree = ast.parse(source)
cave = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "cave")
body = ast.get_source_segment(source, cave)
for marker in (
    "strata_sx, strata_sy = w / 360.0, h / 570.0",
    "base_y=round((90+band*62+int(strata_rng.integers(-11,12)))*strata_sy)",
    "slope=round(int(strata_rng.integers(-17,18))*strata_sy)",
    "offset=round(int(strata_rng.integers(14,42))*strata_sy)",
    "joint_y+round(27*strata_sy)",
    "width=max(1,round(2*strata_sx))",
):
    if marker not in body:
        raise AssertionError(f"Missing scalable strata contract: {marker}")

checks = 0
for w, h in ((120,190), (240,360), (320,480), (360,570),
             (1080,1920), (1272,2772)):
    sx, sy = w/360, h/570
    margin = max(4, min(70, w//5))
    for band in range(7):
        for jitter in (-11, 11):
            for slope0 in (-17, 17):
                for offset0 in (14, 41):
                    y = round((90+band*62+jitter)*sy)
                    slope = round(slope0*sy)
                    offset = round(offset0*sy)
                    # The last band and its deepest branch must remain on canvas.
                    for py in (y, y+slope, y+offset,
                               y+slope+offset//5+round(27*sy)):
                        assert 0 <= py < h, (w,h,band,py)
                        checks += 1
                    for left_end in (max(2,margin//2), margin):
                        right_start = w-left_end
                        for joint_step in (1,8):
                            joint_x = min(w-1,right_start+max(1,round(joint_step*sx)))
                            for px in (joint_x,
                                       max(right_start,joint_x-max(1,round(5*sx))),
                                       max(right_start,joint_x-max(1,round(4*sx)))):
                                assert right_start <= px < w
                                checks += 1
print(f"PASS: {checks} scalable lithology coordinate checks")
