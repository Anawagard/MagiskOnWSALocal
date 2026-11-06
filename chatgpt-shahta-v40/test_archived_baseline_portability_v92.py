"""Regression checks for portable TAR member names; no Android build required."""
import io
import tarfile
import unittest

from audit_archived_baseline_v83 import inspect_tar_members


def validate(names):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as tar:
        for name in names:
            info = tarfile.TarInfo(name)
            info.size = 1
            tar.addfile(info, io.BytesIO(b"x"))
    stream.seek(0)
    with tarfile.open(fileobj=stream, mode="r:") as tar:
        return inspect_tar_members(tar)


class PortableArchiveNames(unittest.TestCase):
    def test_reserved_windows_device_names(self):
        for name in ("CON", "con.txt", "PRN.log", "AUX", "NUL", "COM1.txt", "LPT9.cfg"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate(["app/" + name])

    def test_unicode_canonical_equivalence(self):
        with self.assertRaises(ValueError):
            validate(["app/caf\u00e9.txt", "app/cafe\u0301.txt"])

    def test_unicode_parent_equivalence(self):
        with self.assertRaises(ValueError):
            validate(["app/caf\u00e9/a.txt", "app/cafe\u0301/b.txt"])

    def test_safe_names(self):
        files = validate(["app/ore_01.png", "app/ore_02.png"])
        self.assertEqual(len(files), 2)


if __name__ == "__main__":
    unittest.main()
