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

    def test_generator_must_immediately_precede_raster_patch(self):
        reordered = [self.steps[0], self.steps[2], self.steps[1], self.steps[3]]
        with self.assertRaisesRegex(ValueError, "immediately precede"):
            replay.source_steps(self.workflow(reordered))

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


class ReplayContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.gradle = self.root / replay.GRADLE
        self.java = self.root / replay.JAVA
        self.activity = self.root / "chatgpt-shahta-v33/project/app/src/main/java/com/bezdna/mine/MainActivity.java"
        for path in (self.gradle, self.java, self.activity):
            path.parent.mkdir(parents=True, exist_ok=True)
        self.gradle.write_text('versionCode 46\nversionName "6.9"\nsigningConfig signingConfigs.shahtaDebug\n', encoding="utf-8")
        self.java.write_text('public void save() {}\nprivate void rebirth() {}\ngetSharedPreferences("mine_save_v1", 0);\n', encoding="utf-8")
        self.activity.write_bytes(b"updated import/export")

    def test_valid_replay_contract(self):
        replay.verify_replayed_source(self.root, b"original")

    def test_rejects_version_drift(self):
        self.gradle.write_text(self.gradle.read_text().replace("versionCode 46", "versionCode 47"))
        with self.assertRaisesRegex(AssertionError, "not v6.9"):
            replay.verify_replayed_source(self.root, b"original")

    def test_rejects_missing_save_key(self):
        self.java.write_text(self.java.read_text().replace("mine_save_v1", "mine_save_v2"))
        with self.assertRaisesRegex(AssertionError, "game-state contract"):
            replay.verify_replayed_source(self.root, b"original")

    def test_rejects_signing_drift(self):
        self.gradle.write_text(self.gradle.read_text().replace("shahtaDebug", "release"))
        with self.assertRaisesRegex(AssertionError, "debug signing"):
            replay.verify_replayed_source(self.root, b"original")

    def test_rejects_missing_import_export_change(self):
        with self.assertRaisesRegex(AssertionError, "import/export"):
            replay.verify_replayed_source(self.root, b"updated import/export")


if __name__ == "__main__":
    unittest.main()
