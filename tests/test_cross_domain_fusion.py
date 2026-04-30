from __future__ import annotations

from pathlib import Path

from abraxas.fusion.fusion_engine import fuse_signals
from abraxas.fusion.models import clamp01


def test_deterministic_output() -> None:
    signals = [{"schema_version": "CrossDomainSignal.v1", "signal_id": "s1", "domain": "oracle", "polarity": "positive", "magnitude": 1.0, "confidence": 0.5, "freshness": 1.0}]
    assert fuse_signals(signals) == fuse_signals(signals)


def test_clamping_works() -> None:
    assert clamp01(-5) == 0.0
    assert clamp01(3) == 1.0


def test_dominant_domain_and_conflict_detection() -> None:
    signals = [
        {"schema_version": "CrossDomainSignal.v1", "signal_id": "a", "domain": "oracle", "polarity": "positive", "magnitude": 1, "confidence": 1, "freshness": 1},
        {"schema_version": "CrossDomainSignal.v1", "signal_id": "b", "domain": "operator", "polarity": "negative", "magnitude": 0.5, "confidence": 1, "freshness": 1},
    ]
    report = fuse_signals(signals)
    assert report["dominant_domain"] == "oracle"
    assert report["conflicts"][0]["type"] == "POLARITY_CONFLICT"


def test_empty_input_not_computable() -> None:
    report = fuse_signals([])
    assert report["status"] == "NOT_COMPUTABLE"


def test_unknown_domains_and_authority() -> None:
    signals = [{"schema_version": "CrossDomainSignal.v1", "signal_id": "u1", "domain": "unknown", "polarity": "neutral", "magnitude": 1, "confidence": 1, "freshness": 1}]
    report = fuse_signals(signals)
    assert report["unknown_domains"] == ["u1"]
    assert report["authority"] == "CANDIDATE_ONLY"


def test_no_portfolio_file_created() -> None:
    assert not Path("abraxas/pse/portfolio.py").exists()
