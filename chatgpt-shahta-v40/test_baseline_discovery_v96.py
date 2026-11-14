"""Source-only regression checks for locating the actual Android project root.

Run: python3 chatgpt-shahta-v40/test_baseline_discovery_v96.py
No Gradle, Android tools, APKs or network access.
"""
from pathlib import Path
import ast
import os
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "verify_modernist_patch_chain.py"


def load_locator():
    """Compile only the locator function, never execute the integration runner."""
    module = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    locator = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "locate_project"
    )
    isolated = ast.Module(body=[locator], type_ignores=[])
    ast.fix_missing_locations(isolated)
    namespace = {"Path": Path, "os": os}
    exec(compile(isolated, str(SOURCE), "exec"), namespace)
    return namespace


def make_project(root, version="chatgpt-shahta-v33"):
    project = root / version / "project"
    java = project / "app/src/main/java/com/bezdna/mine"
    java.mkdir(parents=True)
    (java / "MineView.java").write_text("class MineView {}", encoding="utf-8")
    (java / "MainActivity.java").write_text("class MainActivity {}", encoding="utf-8")
    (project / "app/build.gradle").write_text("apply plugin: 'com.android.application'", encoding="utf-8")
    return project


class BaselineDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.original = os.environ.pop("SHAHTA_BASELINE_PROJECT", None)
        self.addCleanup(self.restore_environment)

    def restore_environment(self):
        os.environ.pop("SHAHTA_BASELINE_PROJECT", None)
        if self.original is not None:
            os.environ["SHAHTA_BASELINE_PROJECT"] = self.original

    def test_discovers_project_not_version_parent(self):
        project = make_project(self.root)
        ns = load_locator()
        ns.update(REPO=self.root, DEFAULT_PROJECT=self.root / "missing" / "project")
        self.assertEqual(ns["locate_project"](), project.resolve())

    def test_incomplete_default_does_not_mask_valid_baseline(self):
        default = self.root / "chatgpt-shahta-v33" / "project"
        default.mkdir(parents=True)
        valid = make_project(self.root, "chatgpt-shahta-v34")
        ns = load_locator()
        ns.update(REPO=self.root, DEFAULT_PROJECT=default)
        self.assertEqual(ns["locate_project"](), valid.resolve())

    def test_explicit_project_override(self):
        project = make_project(self.root)
        os.environ["SHAHTA_BASELINE_PROJECT"] = str(project)
        ns = load_locator()
        ns.update(REPO=self.root / "unused", DEFAULT_PROJECT=self.root / "missing")
        self.assertEqual(ns["locate_project"](), project.resolve())

    def test_explicit_incomplete_project_fails_closed(self):
        incomplete = self.root / "incomplete" / "project"
        incomplete.mkdir(parents=True)
        os.environ["SHAHTA_BASELINE_PROJECT"] = str(incomplete)
        ns = load_locator()
        ns.update(REPO=self.root, DEFAULT_PROJECT=self.root / "missing")
        with self.assertRaisesRegex(SystemExit, "not a complete Android project"):
            ns["locate_project"]()

    def test_explicit_override_does_not_fallback(self):
        make_project(self.root)
        incomplete = self.root / "incomplete" / "project"
        incomplete.mkdir(parents=True)
        os.environ["SHAHTA_BASELINE_PROJECT"] = str(incomplete)
        ns = load_locator()
        ns.update(REPO=self.root, DEFAULT_PROJECT=self.root / "chatgpt-shahta-v33" / "project")
        with self.assertRaisesRegex(SystemExit, "missing"):
            ns["locate_project"]()

    def test_ambiguous_baselines_fail_closed(self):
        first = make_project(self.root, "chatgpt-shahta-v33")
        second = make_project(self.root, "chatgpt-shahta-v34")
        # The search examines REPO and its parent, and matches immediate
        # children of each. Both projects therefore share a parent.
        ns = load_locator()
        ns.update(REPO=self.root / "unused", DEFAULT_PROJECT=self.root / "missing")
        with self.assertRaisesRegex(SystemExit, "multiple Android baselines"):
            ns["locate_project"]()
        self.assertNotEqual(first, second)
        self.assertTrue((first / "app/build.gradle").is_file())
        self.assertTrue((second / "app/build.gradle").is_file())


if __name__ == "__main__":
    unittest.main()
