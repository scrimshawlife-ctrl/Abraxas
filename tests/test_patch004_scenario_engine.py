from abx.repair import scenario_engine as se


def test_starter_set_count_and_deterministic():
    a = se.generate_starter_scenarios()
    b = se.generate_starter_scenarios()
    assert len(a) == 6
    assert a == b


def test_zero_execution_and_no_file_mods():
    out = se.run_scenario_batch()
    for r in out["results"]:
        assert r["actions_executed"] == 0
        assert r["files_modified"] == []


def test_unsafe_binding_blocks(monkeypatch):
    original = se.build_patch004_receipt_binding
    def fake(*args, **kwargs):
        b = original(*args, **kwargs)
        b["binding_status"] = "BLOCKED"
        return b
    monkeypatch.setattr(se, "build_patch004_receipt_binding", fake)
    out = se.run_scenario_batch()
    assert out["blocked_count"] == 6


def test_rank_deterministic_and_top_id():
    out = se.run_scenario_batch()
    assert out["top_scenario_id"] == "scn_002"
    assert out["results"][0]["scenario_id"] == "scn_002"


def test_execution_and_mutation_always_false():
    out = se.run_scenario_batch()
    assert out["execution_allowed"] is False
    assert out["runtime_mutation_allowed"] is False
    for r in out["results"]:
        assert r["execution_allowed"] is False
        assert r["runtime_mutation_allowed"] is False
        assert r["safety_flags"] == {"execution_triggered": False, "runtime_mutation": False, "authority_leak_detected": False}
