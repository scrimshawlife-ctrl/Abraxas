import json
from pathlib import Path

from abraxas.perf.ledger import get_perf_ledger_path, write_perf_event
from abraxas.perf.schema import PerfEvent


def test_write_perf_event_serializes_with_model_dump_backend(monkeypatch, tmp_path):
    monkeypatch.setenv("ABRAXAS_ROOT", str(tmp_path))

    event = PerfEvent(
        run_id="RUN-LEDGER-001",
        op_name="acquire",
        source_id="TEST_SOURCE",
        bytes_in=100,
        bytes_out=50,
        duration_ms=1.5,
        cache_hit=True,
        reason_code="bulk_api",
    )

    write_perf_event(event)

    ledger_path = get_perf_ledger_path()
    assert ledger_path == Path(tmp_path) / "out" / "ledger" / "perf_ledger.jsonl"
    assert ledger_path.exists()

    lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])

    assert payload["run_id"] == "RUN-LEDGER-001"
    assert payload["op_name"] == "acquire"
    assert payload["cache_hit"] is True
    assert "timestamp_utc" in payload
