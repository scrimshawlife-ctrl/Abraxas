from pathlib import Path

from abraxas.runes.operators.acquisition_layer import apply_acquire_bulk, apply_acquire_cache_only


def test_acquire_bulk_second_call_hits_cache_and_reuses_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("ABRAXAS_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    first = apply_acquire_bulk(
        source_id="NOAA_NCEI_CDO_V2",
        window_utc="2026-03-27T00:00:00Z",
        params={"station": "AUS", "metric": "temp"},
        run_ctx={"run_id": "RUN-ACQ-001"},
    )
    second = apply_acquire_bulk(
        source_id="NOAA_NCEI_CDO_V2",
        window_utc="2026-03-27T00:00:00Z",
        params={"station": "AUS", "metric": "temp"},
        run_ctx={"run_id": "RUN-ACQ-002"},
    )

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert first["raw_path"] == second["raw_path"]
    assert first["parsed_path"] == second["parsed_path"]

    index_path = tmp_path / "data" / "cas" / "acquisition_cache_index.json"
    assert index_path.exists()



def test_acquire_cache_only_replays_registered_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("ABRAXAS_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    created = apply_acquire_bulk(
        source_id="NOAA_NCEI_CDO_V2",
        window_utc="2026-03-27T00:00:00Z",
        params={"station": "SEA", "metric": "precip"},
        run_ctx={"run_id": "RUN-ACQ-003"},
    )
    cache_key = created["provenance"]["cache_key"]

    replay = apply_acquire_cache_only(
        cache_keys=[cache_key],
        run_ctx={"run_id": "RUN-ACQ-004"},
    )

    assert replay["failures"] == []
    assert len(replay["paths"]) == 2
    assert Path(replay["paths"][0]).exists()
    assert Path(replay["paths"][1]).exists()
