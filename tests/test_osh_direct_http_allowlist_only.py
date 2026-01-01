"""
Tests for direct HTTP allowlist enforcement.
"""

import pytest

from abraxas.osh.transport import fetch_with_fallback, TransportMode
from abraxas.osh.types import OSHFetchJob


def test_osh_direct_http_allowlist_only(tmp_path, monkeypatch):
    monkeypatch.delenv("DECODO_API_KEY", raising=False)

    job = OSHFetchJob(
        job_id="job1",
        run_id="run1",
        action_id="action1",
        url="https://example.com",
        method="GET",
        params={},
        source_label="src",
        vector_node_id=None,
        allowlist_source_id=None,
        budget={},
        provenance={},
    )

    artifact, mode, error = fetch_with_fallback(job, out_raw_dir=str(tmp_path))
    assert artifact is None
    assert mode == TransportMode.OFFLINE_REQUIRED
    assert "direct_http_failed" in (error or "")
