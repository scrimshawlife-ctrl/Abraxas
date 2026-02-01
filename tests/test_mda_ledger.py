from abraxas.mda.ledger import build_run_entry


def test_build_run_entry_hashes_present():
    canon = {"x": 1, "y": 2}
    e = build_run_entry(canon=canon, run_idx=1)

    assert e.run_id == "run_01"
    assert len(e.input_hash) == 64
    assert len(e.dsp_hash) == 64
    assert len(e.fusion_hash) == 64

