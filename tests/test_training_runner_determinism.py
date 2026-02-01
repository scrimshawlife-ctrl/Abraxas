def test_training_runner_is_deterministic(tmp_path):
    from aal_core.training.runner_v1 import run_training_session
    from aal_core.runes.game_theory.ops.load_and_eval_v1 import (
        eval_game_theory_v1,
        load_pack_game_theory_v1,
    )

    ledger = tmp_path / "ledger.jsonl"
    ir = {
        "schema_version": "aal.training.ir.v1",
        "session_id": "t1",
        "pack_id": "aal.rune.game_theory.pack.v1",
        "mode": "diagnostic",
        "vectors": [],
        "options": {"max_items": 2, "seed": 7, "timebox_sec": 5, "strict_mode": True},
        "provenance": {"deterministic": True},
    }
    r1 = run_training_session(ir, load_pack_game_theory_v1, eval_game_theory_v1, ledger)
    r2 = run_training_session(ir, load_pack_game_theory_v1, eval_game_theory_v1, ledger)

    assert r1.score == r2.score
    assert r1.items_seen == r2.items_seen
