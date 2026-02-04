from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


ActionKind = Literal[
    "request_missing_integrity",
    "generate_question_set",
    "enter_observe_only",
]


class ActionCandidate(BaseModel):
    action_id: str
    kind: ActionKind
    title: str
    rationale: List[str] = Field(default_factory=list)
    required_gates: List[str] = Field(default_factory=list)
    expected_entropy_reduction: float
    risk_notes: str
    preview_effect: Dict[str, Any] = Field(default_factory=dict)


def _cap_text(value: str, limit: int = 140) -> str:
    return value[:limit]


def propose_actions(
    *,
    signal_meta: Dict[str, Any],
    compressed: Dict[str, Any],
    requires_human_confirmation: bool,
) -> List[ActionCandidate]:
    actions: List[ActionCandidate] = []
    components = compressed.get("plan_pressure", {}).get("components", {})
    invariance_fail = 1 if components.get("invariance_fail") else 0
    provenance_gap = 1 if components.get("provenance_gap") else 0
    recommended = compressed.get("recommended_mode")
    next_questions = compressed.get("next_questions", [])

    if invariance_fail or provenance_gap:
        rationale: List[str] = []
        if invariance_fail:
            rationale.append("invariance_status=fail contributes to pressure")
        if provenance_gap:
            rationale.append(
                f"provenance_status={signal_meta.get('provenance_status')} contributes to pressure"
            )
        rationale.append(
            f"pressure_components: invariance_fail={invariance_fail} provenance_gap={provenance_gap}"
        )
        required_gates = ["ack_required"] if requires_human_confirmation else ["none"]
        expected = 0.70 if invariance_fail else 0.55
        items_count = max(1, invariance_fail + provenance_gap)
        actions.append(
            ActionCandidate(
                action_id="",
                kind="request_missing_integrity",
                title="Request missing integrity evidence",
                rationale=[_cap_text(r) for r in rationale],
                required_gates=required_gates,
                expected_entropy_reduction=round(expected, 2),
                risk_notes="Low risk; requests integrity artifacts only.",
                preview_effect={"produces": "checklist", "items_count": items_count},
            )
        )

    if next_questions:
        rationale = [
            _cap_text(f"next_questions_count={len(next_questions)} from compress_signal_v0"),
        ]
        actions.append(
            ActionCandidate(
                action_id="",
                kind="generate_question_set",
                title="Generate clarifying question set",
                rationale=rationale,
                required_gates=["none"],
                expected_entropy_reduction=0.45,
                risk_notes="Low risk; generates structured questions only.",
                preview_effect={"produces": "questions", "count": len(next_questions)},
            )
        )

    lane = signal_meta.get("lane")
    if lane == "shadow" or recommended == "observe_only":
        reason = "lane=shadow => observe_only" if lane == "shadow" else "recommended_mode=observe_only"
        actions.append(
            ActionCandidate(
                action_id="",
                kind="enter_observe_only",
                title="Enter observe-only mode",
                rationale=[_cap_text(reason)],
                required_gates=["none"],
                expected_entropy_reduction=0.20,
                risk_notes="No execution; logs only.",
                preview_effect={"produces": "log_only"},
            )
        )

    actions = actions[:3]
    for idx, action in enumerate(actions, start=1):
        action.action_id = f"act_{action.kind}_{idx}"
    return actions
