from __future__ import annotations

from abraxas_ase.leakage_linter import lint_report_for_tier


def test_psychonaut_forbidden_fields() -> None:
    report = {
        "date": "2026-01-24",
        "stats": {"items": 1},
        "verified_sub_anagrams": [{"sub": "war"}],
        "clusters": {"by_item_id": {"1": "c1"}},
        "url": "https://example.com",
    }
    violations = lint_report_for_tier(report, tier="psychonaut")
    assert "report.verified_sub_anagrams forbidden in psychonaut" in violations
    assert "report.clusters forbidden in psychonaut" in violations
    assert any("url" in v for v in violations)


def test_academic_allows_core_fields() -> None:
    report = {
        "date": "2026-01-24",
        "stats": {"items": 1},
        "run_id": "abc",
        "verified_sub_anagrams": [],
        "clusters": {"by_item_id": {}},
    }
    violations = lint_report_for_tier(report, tier="academic")
    assert violations == []
