"""Source-only checks for the historical release-step parser; no Android tools."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import replay_baseline_source_only as replay


class ReplayOrderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo_patch = patch.object(replay, "REPO", self.root)
        self.repo_patch.start()
        self.addCleanup(self.repo_patch.stop)
        self.steps = [
            "chatgpt-shahta-v33/patch_game.py",
            "chatgpt-shahta-v37/patch_real_audio.py",
            "chatgpt-shahta-v40/generate_raster_v69.py",
            "chatgpt-shahta-v40/patch_raster_v69.py",
        ]
        for name in self.steps:
            file = self.root / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("pass\n", encoding="utf-8")

    def workflow(self, steps):
        return "\n".join("        run: python3 " + name for name in steps)

    def test_extracts_release_order_through_v69_only(self):
        workflow = self.workflow(self.steps + [
            "chatgpt-shahta-v40/patch_full_redesign_v70.py"
        ])
        self.assertEqual(replay.source_steps(workflow), self.steps)

    def test_missing_audio_patch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "audio"):
            replay.source_steps(self.workflow([
                name for name in self.steps if "real_audio" not in name
            ]))

    def test_duplicate_steps_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            replay.source_steps(self.workflow([
                self.steps[0], self.steps[0], *self.steps[1:]
            ]))

    def test_missing_terminal_patch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "terminal"):
            replay.source_steps(self.workflow(self.steps[:-1]))

    def test_syntax_error_in_source_patch_is_rejected(self):
        (self.root / self.steps[1]).write_text("def invalid(:\n", encoding="utf-8")
        with self.assertRaises(SyntaxError):
            replay.source_steps(self.workflow(self.steps))

    def test_missing_source_patch_is_rejected(self):
        (self.root / self.steps[1]).unlink()
        with self.assertRaises(FileNotFoundError):
            replay.source_steps(self.workflow(self.steps))


if __name__ == "__main__":
    unittest.main()
