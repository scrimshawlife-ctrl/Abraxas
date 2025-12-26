from __future__ import annotations

import json
from pathlib import Path

from abraxas.evolve.promotion_builder import build_promotion_packet


def test_promotion_packet_snapshot_gate(tmp_path: Path):
    run_id = "r1"
    out_dir = tmp_path / "promotions"

    epp = tmp_path / "epp.json"
    evog = tmp_path / "evog.json"
    rim = tmp_path / "manifest.json"
    cand = tmp_path / "candidate.json"

    epp.write_text(json.dumps({"pack_id": "p1"}), encoding="utf-8")
    evog.write_text(
        json.dumps(
            {
                "pack_id": "p1",
                "ts": "t",
                "promote_recommended": False,
                "replay": {"metric_deltas": {}},
            }
        ),
        encoding="utf-8",
    )
    rim.write_text(
        json.dumps({"version": "rim.v0.1", "totals": {"items": 1}}),
        encoding="utf-8",
    )
    cand.write_text(
        json.dumps({"version": "candidate_policy.v0.1", "overlay": {"intents": {}}}),
        encoding="utf-8",
    )

    json_path, md_path, canon_path, meta = build_promotion_packet(
        run_id=run_id,
        out_dir=str(out_dir),
        epp_path=str(epp),
        evogate_path=str(evog),
        rim_manifest_path=str(rim),
        candidate_policy_path=str(cand),
        emit_canon_snapshot=True,
        force=False,
    )
    assert Path(json_path).exists()
    assert Path(md_path).exists()
    assert canon_path is None
    assert meta["emit_canon_snapshot"] is False
