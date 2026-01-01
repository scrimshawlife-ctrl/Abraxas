from __future__ import annotations

from pathlib import Path

from abraxas.osh.transport import TransportMode, fetch_with_fallback
from abraxas.osh.types import OSHFetchJob


def test_fallback_to_direct_http_when_decodo_missing(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("DECODO_API_KEY", raising=False)

    job = OSHFetchJob(
        job_id="j1",
        run_id="r1",
        action_id="a1",
        url="https://example.invalid/should_fail",
        method="POST",
        params={},
        source_label="s1",
        vector_node_id="node1",
        allowlist_source_id="allow1",
        budget={"timeout_s": 1},
        provenance={},
    )
    art, mode, note = fetch_with_fallback(job, out_raw_dir=str(tmp_path))
    assert art is None
    assert mode == TransportMode.OFFLINE_REQUIRED
    assert note is not None
    assert "decodo_unavailable" in note


def test_direct_http_requires_allowlist_source_id(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("DECODO_API_KEY", raising=False)
    job = OSHFetchJob(
        job_id="j2",
        run_id="r1",
        action_id="a1",
        url="https://example.invalid/should_fail",
        method="POST",
        params={},
        source_label="s1",
        vector_node_id=None,
        allowlist_source_id=None,
        budget={"timeout_s": 1},
        provenance={},
    )
    art, mode, note = fetch_with_fallback(job, out_raw_dir=str(tmp_path))
    assert art is None
    assert mode == TransportMode.OFFLINE_REQUIRED
    assert note is not None
    assert "missing allowlist_source_id" in note
