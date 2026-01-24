from __future__ import annotations

from abraxas_ase.candidates import CandidateRec, write_candidates_jsonl


def test_candidates_snapshot_is_sorted(tmp_path):
    p = tmp_path / "c.jsonl"
    recs = [
        CandidateRec("b","subword","2026-01-01","2026-01-01",1,["ap"],["e"],0.0,1.0,0.0,1,"candidate"),
        CandidateRec("a","subword","2026-01-01","2026-01-01",1,["ap"],["e"],0.0,1.0,0.0,1,"candidate"),
    ]
    write_candidates_jsonl(str(p), recs)
    txt = p.read_text(encoding="utf-8").splitlines()
    assert '"candidate":"a"' in txt[0] or '"candidate":"a"' in txt[0]
