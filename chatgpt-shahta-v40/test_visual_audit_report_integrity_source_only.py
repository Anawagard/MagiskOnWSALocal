"""Source-only mathematical checks for the 48-image visual audit report.

No Android SDK, Gradle, emulator, APK, or GitHub Actions involved.
Run: python -m unittest test_visual_audit_report_integrity_source_only.py
"""
import math
import unittest

from audit_visual_diversity import BIOMES, ORES


def validate_report(report):
    """Check that nearest-neighbor metadata is internally consistent."""
    for group, expected in (("biomes", BIOMES), ("ores", ORES)):
        entries = report[group]
        neighbors = report[group + "_nearest_neighbors"]
        pair = report[group + "_closest_pair"]
        names = [entry["file"] for entry in entries]
        if names != expected:
            raise ValueError(group + ": asset ordering or count mismatch")
        if len({entry["sha256"] for entry in entries}) != 24:
            raise ValueError(group + ": duplicate asset hashes")
        if [item["file"] for item in neighbors] != expected:
            raise ValueError(group + ": neighbor ordering or count mismatch")
        for item in neighbors:
            if item["nearest_file"] not in expected or item["nearest_file"] == item["file"]:
                raise ValueError(group + ": invalid neighbor reference")
            distance = item["mean_channel_delta"]
            if not isinstance(distance, (float, int)) or not math.isfinite(distance) or distance < 1.5:
                raise ValueError(group + ": invalid neighbor distance")
        pair_names = pair["files"]
        if len(pair_names) != 2 or len(set(pair_names)) != 2 or any(name not in expected for name in pair_names):
            raise ValueError(group + ": invalid closest pair")
        minimum = min(item["mean_channel_delta"] for item in neighbors)
        if not math.isclose(pair["mean_channel_delta"], minimum, abs_tol=0.0011):
            raise ValueError(group + ": closest-pair distance inconsistent with neighbors")


class ReportIntegrityTests(unittest.TestCase):
    def make_report(self):
        result = {}
        for group, names in (("biomes", BIOMES), ("ores", ORES)):
            result[group] = [{"file": name, "sha256": str(i)} for i, name in enumerate(names)]
            result[group + "_nearest_neighbors"] = [
                {"file": name, "nearest_file": names[(i + 1) % 24],
                 "mean_channel_delta": 2.0 if i < 2 else 5.0}
                for i, name in enumerate(names)
            ]
            result[group + "_closest_pair"] = {
                "files": names[:2], "mean_channel_delta": 2.0,
            }
        return result

    def test_valid_report(self):
        validate_report(self.make_report())

    def test_missing_neighbor(self):
        report = self.make_report()
        report["ores_nearest_neighbors"].pop()
        with self.assertRaises(ValueError):
            validate_report(report)

    def test_nan_distance(self):
        report = self.make_report()
        report["biomes_nearest_neighbors"][0]["mean_channel_delta"] = float("nan")
        with self.assertRaises(ValueError):
            validate_report(report)

    def test_inconsistent_closest_pair(self):
        report = self.make_report()
        report["ores_closest_pair"]["mean_channel_delta"] = 4.0
        with self.assertRaises(ValueError):
            validate_report(report)

    def test_unknown_neighbor(self):
        report = self.make_report()
        report["ores_nearest_neighbors"][0]["nearest_file"] = "missing.png"
        with self.assertRaises(ValueError):
            validate_report(report)


if __name__ == "__main__":
    unittest.main()
