"""Source-only v7.9 regression suite; no Android SDK or Gradle required.

Run: python3 -m unittest discover -s chatgpt-shahta-v40 -p 'test_v79_atomic.py'
Also run with python3 -O to ensure failures cannot be optimized away.
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("patch_modernist_v79.py")


def load_patch():
    spec = importlib.util.spec_from_file_location("shahta_patch_v79_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AtomicToastPatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        self.java = self.project / "MineView.java"
        self.gradle = self.project / "build.gradle"
        self.patch = load_patch()
        self.patch.source = self.java
        self.patch.root = self.project
        self.valid_gradle = (
            "applicationId 'com.bezdna.mine'\n"
            "signingConfig signingConfigs.shahtaDebug\n"
        )
        self.valid_java = (
            "v71Scale()\n"
            "else if(x>=105&&x<=330&&y>=210&&y<=440)\n"
            'getSharedPreferences("mine_save_v1"\n'
            "public void save()\n"
            "private void rebirth()\n"
            + self.patch.old + "\n"
        )
        self.java.write_text(self.valid_java, encoding="utf-8")
        self.gradle.write_text(self.valid_gradle, encoding="utf-8")

    def test_valid_patch_replaces_only_toast(self):
        self.patch.apply()
        actual = self.java.read_text(encoding="utf-8")
        self.assertEqual(actual, self.valid_java.replace(self.patch.old, self.patch.new, 1))
        self.assertEqual(self.gradle.read_text(encoding="utf-8"), self.valid_gradle)
        self.assertFalse(list(self.project.glob(".mineview-v79-*")))

    def test_duplicate_anchor_rejected_without_write(self):
        initial = self.valid_java + self.patch.old
        self.java.write_text(initial, encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.patch.apply()
        self.assertEqual(self.java.read_text(encoding="utf-8"), initial)

    def test_missing_persistence_contract_rejected(self):
        initial = self.valid_java.replace("public void save()", "public void store()")
        self.java.write_text(initial, encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.patch.apply()
        self.assertEqual(self.java.read_text(encoding="utf-8"), initial)

    def test_wrong_signing_config_rejected(self):
        initial = self.valid_gradle.replace("shahtaDebug", "release")
        self.gradle.write_text(initial, encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.patch.apply()
        self.assertEqual(self.java.read_text(encoding="utf-8"), self.valid_java)
        self.assertEqual(self.gradle.read_text(encoding="utf-8"), initial)

    def test_repeat_application_rejected(self):
        self.patch.apply()
        once = self.java.read_bytes()
        with self.assertRaises(RuntimeError):
            self.patch.apply()
        self.assertEqual(self.java.read_bytes(), once)

    def test_geometry_rejects_overlap(self):
        with patch.dict(self.patch.TOAST_Y, {0: 220}):
            with self.assertRaises(RuntimeError):
                self.patch.validate_toast_geometry()

    def test_geometry_accepts_five_pages(self):
        self.patch.validate_toast_geometry()


if __name__ == "__main__":
    unittest.main()
