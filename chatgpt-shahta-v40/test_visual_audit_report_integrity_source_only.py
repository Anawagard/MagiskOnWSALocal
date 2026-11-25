"""Source-only mathematical checks for the 48-image visual audit report.

No Android SDK, Gradle, emulator, APK, or GitHub Actions involved.
Run: python -m unittest test_visual_audit_report_integrity_source_only.py
"""
import math
import re
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
        expected_size = [360, 570] if group == "biomes" else [300, 300]
        for entry in entries:
            digest = entry["sha256"]
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ValueError(group + ": malformed SHA-256 digest")
            if entry["size"] != expected_size:
                raise ValueError(group + ": unexpected decoded raster dimensions")
            occupancy = entry["alpha_occupancy"]
            if not isinstance(occupancy, (int, float)) or not math.isfinite(occupancy):
                raise ValueError(group + ": invalid alpha occupancy")
            if group == "biomes" and occupancy != 1.0:
                raise ValueError(group + ": biome must be opaque")
            if group == "ores" and not 0.12 <= occupancy <= 0.85:
                raise ValueError(group + ": ore silhouette occupancy out of range")
        if [item["file"] for item in neighbors] != expected:
            raise ValueError(group + ": neighbor ordering or count mismatch")
        for item in neighbors:
            if item["nearest_file"] not in expected or item["nearest_file"] == item["file"]:
                raise ValueError(group + ": invalid neighbor reference")
            distance = item["mean_channel_delta"]
            if not isinstance(distance, (float, int)) or not math.isfinite(distance) or not 1.5 <= distance <= 255.0:
                raise ValueError(group + ": invalid neighbor distance")
        pair_names = pair["files"]
        if len(pair_names) != 2 or len(set(pair_names)) != 2 or any(name not in expected for name in pair_names):
            raise ValueError(group + ": invalid closest pair")
        if not isinstance(pair["mean_channel_delta"], (int, float)) or not math.isfinite(pair["mean_channel_delta"]):
            raise ValueError(group + ": nonfinite closest-pair distance")
        # Every globally closest pair must appear in at least one nearest-
        # neighbor record, including when several pairs share the minimum.
        if not any(item["file"] in pair_names
                   and item["nearest_file"] in pair_names
                   and item["file"] != item["nearest_file"]
                   and math.isclose(item["mean_channel_delta"], pair["mean_channel_delta"],
                                    abs_tol=0.0011) for item in neighbors):
            raise ValueError(group + ": closest pair absent from nearest neighbors")
        minimum = min(item["mean_channel_delta"] for item in neighbors)
        if not math.isclose(pair["mean_channel_delta"], minimum, abs_tol=0.0011):
            raise ValueError(group + ": closest-pair distance inconsistent with neighbors")


class ReportIntegrityTests(unittest.TestCase):
    def make_report(self):
        result = {}
        for group, names in (("biomes", BIOMES), ("ores", ORES)):
            result[group] = [{"file": name, "sha256": f"{i:064x}", "size": [360, 570] if group == "biomes" else [300, 300], "alpha_occupancy": 1.0 if group == "biomes" else 0.5} for i, name in enumerate(names)]
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

    def test_bad_sha256(self):
        report = self.make_report()
        report["ores"][0]["sha256"] = "not-a-digest"
        with self.assertRaises(ValueError):
            validate_report(report)

    def test_wrong_dimensions(self):
        report = self.make_report()
        report["biomes"][0]["size"] = [570, 360]
        with self.assertRaises(ValueError):
            validate_report(report)

    def test_invisible_ore(self):
        report = self.make_report()
        report["ores"][0]["alpha_occupancy"] = 0.01
        with self.assertRaises(ValueError):
            validate_report(report)

    def test_closest_pair_not_a_neighbor(self):
        report = self.make_report()
        report["biomes_closest_pair"]["files"] = [BIOMES[8], BIOMES[9]]
        with self.assertRaises(ValueError):
            validate_report(report)

    def test_unknown_neighbor(self):
        report = self.make_report()
        report["ores_nearest_neighbors"][0]["nearest_file"] = "missing.png"
        with self.assertRaises(ValueError):
            validate_report(report)


if __name__ == "__main__":
    unittest.main()
