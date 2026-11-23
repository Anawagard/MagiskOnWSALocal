"""Source-only regression: mirrored art must not count as distinct assets."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from audit_visual_diversity import BIOMES, ORES, audit


class MirrorDuplicateTests(unittest.TestCase):
    def test_horizontal_vertical_and_180_degree_mirrors_rejected(self):
        for axis in (0, 1, (0, 1)):
            with self.subTest(axis=axis), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                names = BIOMES + ORES
                for name in names:
                    (folder / name).touch()
                rng = np.random.default_rng(20261123)
                thumbs = {
                    name: rng.integers(0, 256, (32, 32, 4 if name.endswith(".png") else 3)).astype(np.float32)
                    for name in names
                }
                thumbs[ORES[1]] = np.flip(thumbs[ORES[0]], axis=axis).copy()

                def fake_inspect(path, ore):
                    return {"file": path.name}, thumbs[path.name]

                with patch("audit_visual_diversity.inspect", side_effect=fake_inspect):
                    with self.assertRaisesRegex(ValueError, "mirrored duplicate ore_00.png / ore_01.png"):
                        audit(folder)


if __name__ == "__main__":
    unittest.main()
