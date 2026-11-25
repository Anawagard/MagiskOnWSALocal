"""Reject impossible empty-alpha measurements before publishing ore diagnostics.

Source-only regression; no Android build or asset writes.
"""
from audit_ore_biome_composites_source_only import COUNT, summarize_risks


def fixture():
    return [
        {"biome": biome, "ore": ore, "score": 0.2,
         "visible_coverage": 0.5, "weakest_decile": 0.1,
         "core_coverage": 0.25, "core_mean_contrast": 0.2,
         "core_weakest_decile": 0.1, "core_low_contrast_fraction": 0.0}
        for biome in range(1, COUNT + 1)
        for ore in range(1, COUNT + 1)
    ]


def test_zero_visible_coverage_rejected():
    rows = fixture()
    rows[0]["visible_coverage"] = 0.0
    try:
        summarize_risks(rows, require_complete=True)
    except ValueError as exc:
        assert "Empty visible ore coverage" in str(exc)
    else:
        raise AssertionError("complete report accepted an empty visible sprite")


def test_valid_complete_matrix_accepted():
    summary = summarize_risks(fixture(), require_complete=True)
    assert summary["risk_pairs"] == 0
    assert summary["unscorable_core_pairs"] == 0


if __name__ == "__main__":
    test_zero_visible_coverage_rejected()
    test_valid_complete_matrix_accepted()
    print("PASS: nonzero visible coverage validation (source-only)")
