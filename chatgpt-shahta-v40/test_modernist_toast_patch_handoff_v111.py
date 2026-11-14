"""Source-only contract for the v7.8 -> v7.9 notification handoff.

Checks the actual patch templates, without Gradle, Android or asset generation.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent


def templates(version):
    tree = ast.parse((ROOT / f"patch_modernist_v{version}.py").read_text(encoding="utf-8"))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("old", "new"):
                    found[target.id] = ast.literal_eval(node.value)
    if set(found) != {"old", "new"}:
        raise AssertionError(f"v{version} must have one old/new patch pair")
    return found


class ToastPatchHandoff(unittest.TestCase):
    def test_v78_output_is_exact_v79_input(self):
        previous = templates(78)
        current = templates(79)
        # v7.8 edits three lines inside an existing Java notification block.
        # v7.9 replaces that entire block. Check the actual handoff, not
        # merely whether both scripts mention the same toast coordinates.
        wrapped = (
            "        if(System.currentTimeMillis()<toastUntil){\n"
            + previous["new"] + "\n"
            + "        }"
        )
        self.assertEqual(current["old"], wrapped)
        self.assertEqual(current["old"].count(previous["new"]), 1)

    def test_v79_keeps_one_notification_guard(self):
        current = templates(79)
        for name in ("old", "new"):
            with self.subTest(template=name):
                self.assertEqual(
                    current[name].count("if(System.currentTimeMillis()<toastUntil){"), 1
                )
                self.assertTrue(current[name].rstrip().endswith("}"))
        self.assertNotEqual(current["old"], current["new"])

    def test_replacement_preserves_neighbors(self):
        current = templates(79)
        before, after = "BEFORE_SENTINEL\n", "\nAFTER_SENTINEL"
        sample = before + current["old"] + after
        self.assertEqual(sample.count(current["old"]), 1)
        result = sample.replace(current["old"], current["new"], 1)
        self.assertEqual(result, before + current["new"] + after)
        self.assertNotIn(current["old"], result)


if __name__ == "__main__":
    unittest.main()
