from __future__ import annotations

from typing import Any, Dict

from aal_core.training.runner_v1 import run_training_session
from aal_core.runes.game_theory.ops.load_and_eval_v1 import (
    eval_game_theory_v1,
    load_pack_game_theory_v1,
)


def oracle_attach_training_shadow(oracle_packet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs a tiny integrity check on training packs and logs it locally.
    Attaches results under oracle_packet['shadow']['training'].
    """
    training_ir = {
        "schema_version": "aal.training.ir.v1",
        "session_id": oracle_packet.get("provenance", {}).get("run_id", "oracle_run_unknown"),
        "pack_id": "aal.rune.game_theory.pack.v1",
        "mode": "diagnostic",
        "vectors": [],
        "options": {"max_items": 3, "seed": 23, "timebox_sec": 10, "strict_mode": True},
        "provenance": {"source": "oracle_run", "deterministic": True},
    }

    res = run_training_session(training_ir, load_pack_game_theory_v1, eval_game_theory_v1)
    shadow = oracle_packet.setdefault("oracle_packet_v0_1", {}).setdefault("shadow", {})
    shadow.setdefault("training", {})["game_theory_pack_v1"] = {
        "score": res.score,
        "items_seen": res.items_seen,
        "findings": res.findings,
        "provenance": res.provenance,
    }
    return oracle_packet
