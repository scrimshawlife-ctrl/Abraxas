from __future__ import annotations

from abraxas_ase.candidates import CandidateRec, load_candidates_jsonl, write_candidates_jsonl


def test_candidates_snapshot_is_sorted(tmp_path) -> None:
    path = tmp_path / "candidates.jsonl"
    recs = [
        CandidateRec("b", "subword", "2026-01-01", "2026-01-01", 1, ["ap"], ["e"], 0.0, 1.0, 0.0, 1, "candidate"),
        CandidateRec("a", "subword", "2026-01-01", "2026-01-01", 1, ["ap"], ["e"], 0.0, 1.0, 0.0, 1, "candidate"),
    ]
    write_candidates_jsonl(str(path), recs)
    loaded = load_candidates_jsonl(str(path))
    keys = list(loaded.keys())
    assert keys == [("subword", "a"), ("subword", "b")]
