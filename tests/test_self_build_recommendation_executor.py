from __future__ import annotations

from pathlib import Path

from abraxas.registry.self_build_recommendation_executor import run_self_build_recommendation_executor


def _load_action_by_type(action_type: str) -> str | None:
    path = Path("out/registry/self_build_operator_action_recommendations.latest.json")
    if not path.exists():
        return None
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    for action in data.get("actions", []):
        if action.get("action_type") == action_type:
            return action.get("action_id")
    return None


def test_unknown_action_fails_closed() -> None:
    result = run_self_build_recommendation_executor("action-does-not-exist")
    assert result["status"] == "NOT_COMPUTABLE"


def test_approve_one_writes_approval_input() -> None:
    action_id = _load_action_by_type("REQUEST_APPROVAL")
    if action_id is None:
        return
    result = run_self_build_recommendation_executor(action_id)
    assert result["status"] == "EXECUTED"
    assert result["action_type"] == "APPROVE_ONE"
    assert isinstance(result.get("approval_write"), dict)


def test_hold_noop() -> None:
    action_id = _load_action_by_type("HOLD_APPROVAL_FOR_REVIEW")
    if action_id is None:
        return
    result = run_self_build_recommendation_executor(action_id)
    assert result["status"] == "EXECUTED"
    assert result["action_type"] == "HOLD"
    assert result["approval_write"]["status"] == "NO_OP"


def test_authority_constraints() -> None:
    result = run_self_build_recommendation_executor("action-does-not-exist")
    assert result["authority"] == {
        "mutation": False,
        "promotion": False,
        "execution": False,
        "operator_intent_write": True,
        "artifact_mutation": False,
        "recommendation_execution_only": True,
    }
