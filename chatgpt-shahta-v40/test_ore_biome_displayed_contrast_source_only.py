"""Regression tests for actual displayed ore/biome contrast; no Android build."""
import numpy as np
from audit_ore_biome_composites_source_only import contrast_score


def rgb(value, size=4):
    return np.full((size, size, 3), value, dtype=np.uint8)


def ore(rgb_value, alpha, size=4):
    result = np.empty((size, size, 4), dtype=np.uint8)
    result[:, :, :3] = rgb_value
    result[:, :, 3] = alpha
    return result


def test_opaque_difference():
    assert abs(contrast_score(rgb(0), ore(255, 255)) - 1.0) < 1e-6
    assert abs(contrast_score(rgb(80), ore(80, 255))) < 1e-6


def test_transparency_scales_displayed_difference():
    score = contrast_score(rgb(0), ore(255, 128))
    assert abs(score - 128 / 255) < 1e-6


def test_transparent_rgb_does_not_affect_score():
    image = ore(255, 255)
    image[0, 0, :3] = 255
    image[0, 0, 3] = 0
    score = contrast_score(rgb(0), image)
    assert abs(score - 1.0) < 1e-6


def test_empty_sprite_rejected():
    try:
        contrast_score(rgb(0), ore(255, 0))
    except ValueError as exc:
        assert "empty ore sprite" in str(exc)
    else:
        raise AssertionError("fully transparent sprite was accepted")


if __name__ == "__main__":
    test_opaque_difference()
    test_transparency_scales_displayed_difference()
    test_transparent_rgb_does_not_affect_score()
    test_empty_sprite_rejected()
    print("PASS: displayed-pixel contrast regression (source-only)")
