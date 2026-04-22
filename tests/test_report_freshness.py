from __future__ import annotations

from abx.report_freshness import evaluate_freshness, resolve_max_age_seconds


def test_stale_detection() -> None:
    freshness = evaluate_freshness("2026-04-21T00:00:00Z", "2026-04-21T00:10:01Z", artifact_type="comparison")
    assert freshness["status"] == "OK"
    assert freshness["is_stale"] is True
    assert freshness["age_seconds"] == 601


def test_max_age_enforcement_override(monkeypatch) -> None:
    monkeypatch.setenv("ABRAXAS_REPORT_MAX_AGE_SECONDS", "30")
    assert resolve_max_age_seconds("developer_readiness") == 30
    freshness = evaluate_freshness("2026-04-21T00:00:00Z", "2026-04-21T00:00:31Z", artifact_type="developer_readiness")
    assert freshness["max_age_seconds"] == 30
    assert freshness["is_stale"] is True


def test_missing_timestamp_not_computable() -> None:
    freshness = evaluate_freshness(None, "2026-04-21T00:00:00Z", artifact_type="preflight")
    assert freshness["status"] == "NOT_COMPUTABLE"
    assert freshness["is_stale"] is True
    assert freshness["age_seconds"] == -1


def test_deterministic_output() -> None:
    a = evaluate_freshness("2026-04-21T00:00:00Z", "2026-04-21T00:00:30Z", artifact_type="reporting_cycle")
    b = evaluate_freshness("2026-04-21T00:00:00Z", "2026-04-21T00:00:30Z", artifact_type="reporting_cycle")
    assert a == b
