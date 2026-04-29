from abx.repair.scenario_engine import run_scenario_batch
from abx.repair.scenario_review_queue import build_scenario_review_queue, record_scenario_review_decision


def test_queue_builds_from_batch():
    q = build_scenario_review_queue(run_scenario_batch())
    assert q["schema_version"] == "OperatorScenarioReviewQueue.v1"
    assert q["item_count"] == 6


def test_top_scenario_is_p1_approve():
    q = build_scenario_review_queue(run_scenario_batch())
    top = q["items"][0]
    assert top["priority"] == "P1"
    assert top["recommended_action"] == "APPROVE_FOR_SANDBOX_DESIGN"


def test_other_pass_scenarios_p2_defer():
    q = build_scenario_review_queue(run_scenario_batch())
    others = [i for i in q["items"] if i["recommended_action"] == "DEFER"]
    assert others
    assert all(i["priority"] == "P2" for i in others)


def test_blocked_scenario_maps_to_p1_reject():
    batch = run_scenario_batch()
    batch["results"][0]["scenario_status"] = "BLOCKED"
    q = build_scenario_review_queue(batch)
    blocked = [i for i in q["items"] if i["scenario_id"] == batch["results"][0]["scenario_id"]][0]
    assert blocked["priority"] == "P1"
    assert blocked["recommended_action"] in {"REJECT", "DEFER"}


def test_ordering_deterministic():
    a = build_scenario_review_queue(run_scenario_batch())
    b = build_scenario_review_queue(run_scenario_batch())
    assert [i["review_id"] for i in a["items"]] == [i["review_id"] for i in b["items"]]


def test_flags_always_false_and_receipt_only():
    q = build_scenario_review_queue(run_scenario_batch())
    assert q["execution_allowed"] is False
    assert q["runtime_mutation_allowed"] is False
    assert q["auto_apply_allowed"] is False
    assert all(i["execution_allowed"] is False and i["runtime_mutation_allowed"] is False and i["auto_apply_allowed"] is False for i in q["items"])
    r = record_scenario_review_decision(q, q["items"][0]["review_id"], "APPROVE")
    assert r["schema_version"] == "ScenarioReviewReceipt.v1"
    assert r["files_modified"] == []
    assert r["execution_allowed"] is False
