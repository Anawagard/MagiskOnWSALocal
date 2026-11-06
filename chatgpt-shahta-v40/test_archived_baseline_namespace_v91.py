"""Source-only TAR namespace regression; no Android build or extraction."""
import io
import tarfile
import unittest

from audit_archived_baseline_v83 import inspect_tar_members


def archive_of(entries):
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w") as out:
        for name, kind, size in entries:
            item = tarfile.TarInfo(name)
            item.type = tarfile.DIRTYPE if kind == "dir" else tarfile.REGTYPE
            item.size = 0 if kind == "dir" else size
            if item.size > 0:
                out.addfile(item, io.BytesIO(b"x" * item.size))
            else:
                out.addfile(item)
    data.seek(0)
    return tarfile.open(fileobj=data, mode="r:")


class ArchiveNamespaceTests(unittest.TestCase):
    def check_invalid(self, entries):
        with archive_of(entries) as tar:
            with self.assertRaises(ValueError):
                inspect_tar_members(tar)

    def test_valid_nested_files(self):
        with archive_of([("app", "dir", 0), ("app/build.gradle", "file", 3)]) as tar:
            self.assertEqual(inspect_tar_members(tar), {"app/build.gradle": 3})

    def test_duplicate(self):
        self.check_invalid([("a", "file", 0), ("a", "file", 0)])

    def test_file_as_parent(self):
        self.check_invalid([("a", "file", 0), ("a/b", "file", 0)])

    def test_file_shadows_previous_child(self):
        self.check_invalid([("a/b", "file", 0), ("a", "file", 0)])

    def test_backslash(self):
        self.check_invalid([("app\\..\\escape", "file", 0)])

    def test_dot_segments(self):
        self.check_invalid([("a/../escape", "file", 0)])

    def test_windows_drive_alias(self):
        self.check_invalid([("C:/app/build.gradle", "file", 0)])

    def test_windows_ads_alias(self):
        self.check_invalid([("app/build.gradle:alternate", "file", 0)])

    def test_trailing_dot_or_space(self):
        self.check_invalid([("app./build.gradle", "file", 0)])
        self.check_invalid([("app /build.gradle", "file", 0)])

    def test_repeated_slash(self):
        self.check_invalid([("app//build.gradle", "file", 0)])

    def test_control_character(self):
        self.check_invalid([("app/bad\\x01.gradle", "file", 0)])

    def test_case_insensitive_collision(self):
        self.check_invalid([("app/Build.gradle", "file", 0),
                            ("app/build.gradle", "file", 0)])

    def test_case_insensitive_directory_collision(self):
        self.check_invalid([("App", "dir", 0), ("app", "dir", 0)])

    def test_valid_distinct_casefold_paths(self):
        with archive_of([("app/A.gradle", "file", 0),
                         ("app/B.gradle", "file", 0)]) as tar:
            self.assertEqual(len(inspect_tar_members(tar)), 2)

    def test_symlink(self):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode="w") as out:
            item = tarfile.TarInfo("link")
            item.type = tarfile.SYMTYPE
            item.linkname = "app"
            out.addfile(item)
        data.seek(0)
        with tarfile.open(fileobj=data, mode="r:") as tar:
            with self.assertRaises(ValueError):
                inspect_tar_members(tar)


if __name__ == "__main__":
    unittest.main()
