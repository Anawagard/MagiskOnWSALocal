"""Source-only regression for the complete 24x24 visual review atlas."""
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from preview_all_ore_biome_pairs_source_only import render_atlas


def test_full_atlas_and_atomic_failure():
    with tempfile.TemporaryDirectory() as root:
        root = Path(root)
        assets = root / "assets"
        assets.mkdir()
        output = root / "diagnostics" / "all-pairs.png"
        # Small synthetic fixtures are deliberately the real input dimensions.
        for i in range(24):
            Image.new("RGB", (360, 570), (20 + i, 40, 50)).save(
                assets / f"biome_{i:02d}.jpg", format="JPEG")
            Image.new("RGBA", (300, 300), (210, 150 + i, 40, 200)).save(
                assets / f"ore_{i:02d}.png", format="PNG")
        render_atlas(assets, output, tile=48)
        with Image.open(output) as atlas:
            assert atlas.size == (28 + 24 * 51 + 3, 28 + 24 * 51 + 3)
            assert atlas.getpixel((28 + 23 * 51 + 12, 28 + 23 * 51 + 12)) != (20, 26, 34)
        # Verify every cell maps to its intended biome row and ore column.
        # A transposition or repeated sprite can otherwise pass a size-only test.
        from audit_ore_biome_composites_source_only import (
            ore_backdrop, read_ore, read_rgb, BACKGROUND_SIZE,
        )
        with Image.open(output) as atlas:
            for biome in range(24):
                backdrop = ore_backdrop(
                    read_rgb(assets / f"biome_{biome:02d}.jpg",
                             BACKGROUND_SIZE, "JPEG"), sample_size=48
                ).convert("RGBA")
                for ore in range(24):
                    foreground = read_ore(assets / f"ore_{ore:02d}.png",
                                          sample_size=48)
                    expected_tile = Image.alpha_composite(
                        backdrop, foreground
                    ).convert("RGB")
                    # The center alone cannot detect clipped corners, an
                    # incorrect paste offset, or a repeated edge texture.
                    # Sample the four interior corners and center of every
                    # cell, including the final row and column.
                    for x, y in ((1, 1), (46, 1), (24, 24),
                                 (1, 46), (46, 46)):
                        expected = expected_tile.getpixel((x, y))
                        actual = atlas.getpixel(
                            (28 + ore * 51 + x, 28 + biome * 51 + y)
                        )
                        assert actual == expected, (
                            biome, ore, x, y, actual, expected
                        )
        original = output.read_bytes()
        (assets / "ore_23.png").unlink()
        try:
            render_atlas(assets, output, tile=48)
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("missing production ore was accepted")
        assert output.read_bytes() == original
        for invalid in (True, 47, 257, 96.5):
            try:
                render_atlas(assets, output, tile=invalid)
            except ValueError:
                pass
            else:
                raise AssertionError(f"invalid tile accepted: {invalid}")
        try:
            render_atlas(assets, assets / "bad.png", tile=48)
        except ValueError:
            pass
        else:
            raise AssertionError("production asset overwrite was accepted")


def test_atlas_publish_failure_preserves_previous_output():
    # The atlas is diagnostic output: a failed publish must never destroy a
    # previously generated review image or leave temporary PNGs behind.
    with tempfile.TemporaryDirectory() as root:
        root = Path(root)
        assets = root / "assets"
        assets.mkdir()
        output = root / "diagnostics" / "all-pairs.png"
        output.parent.mkdir()
        original = b"previous-atlas-generation"
        output.write_bytes(original)
        for i in range(24):
            Image.new("RGB", (360, 570), (20 + i, 40, 50)).save(
                assets / f"biome_{i:02d}.jpg", format="JPEG")
            Image.new("RGBA", (300, 300), (210, 150 + i, 40, 200)).save(
                assets / f"ore_{i:02d}.png", format="PNG")
        with patch("preview_all_ore_biome_pairs_source_only.os.replace",
                   side_effect=OSError("simulated atomic publish failure")):
            try:
                render_atlas(assets, output, tile=48)
            except OSError as error:
                assert "simulated atomic publish failure" in str(error)
            else:
                raise AssertionError("failed atlas publication was accepted")
        assert output.read_bytes() == original
        assert sorted(p.name for p in output.parent.iterdir()) == [output.name]


if __name__ == "__main__":
    test_full_atlas_and_atomic_failure()
    test_atlas_publish_failure_preserves_previous_output()
    print("PASS: full 576-pair atlas source-only")
