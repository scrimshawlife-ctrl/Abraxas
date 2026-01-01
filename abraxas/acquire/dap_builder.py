from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .cost_risk import estimate_cost, estimate_risk
from .playbook import load_playbook_yaml, validate_playbook, rule_matches
from .types import (
    AcquisitionAction,
    AcquisitionActionKind,
    DataAcquisitionPlan,
    DataGap,
    GapKind,
)


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json_if_exists(path: str) -> Optional[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


@dataclass(frozen=True)
class DapInputs:
    forecast_scores_path: Optional[str] = None
    regime_scores_path: Optional[str] = None
    component_scores_path: Optional[str] = None
    drift_report_path: Optional[str] = None
    smv_report_path: Optional[str] = None
    integrity_snapshot_path: Optional[str] = None


def detect_gaps(run_id: str, ts: str, inputs: DapInputs) -> List[DataGap]:
    gaps: List[DataGap] = []

    regime = _read_json_if_exists(inputs.regime_scores_path) or {}
    components = _read_json_if_exists(inputs.component_scores_path) or {}
    integrity = _read_json_if_exists(inputs.integrity_snapshot_path) or {}
    drift = _read_json_if_exists(inputs.drift_report_path) or {}

    coverage_rate = _safe_float(regime.get("coverage_rate"))
    coverage_target = 0.75
    if coverage_rate and coverage_rate < coverage_target:
        severity = min(1.0, (coverage_target - coverage_rate) / coverage_target)
        gap_id = _sha(f"{run_id}:{ts}:coverage:{coverage_rate}")[:16]
        gaps.append(
            DataGap(
                gap_id=gap_id,
                kind=GapKind.COVERAGE_GAP,
                topic_key=regime.get("topic_key"),
                horizon=regime.get("horizon") or "H5Y",
                domain=regime.get("domain") or "FORECAST",
                component_ids=list(components.get("missing_components", []))[:10],
                portfolio_ids=list(regime.get("portfolio_ids", ["long_horizon_integrity"])),
                symptoms={"coverage_rate": coverage_rate, "target": coverage_target},
                evidence=[{"artifact": inputs.regime_scores_path, "key": "coverage_rate"}],
                priority=float(0.6 + 0.4 * severity),
                created_ts=ts,
                provenance={"run_id": run_id, "detector": "dap_builder.v0.1"},
            )
        )

    ssi_mean = _safe_float(integrity.get("ssi_mean"))
    quarantined_ratio = _safe_float(integrity.get("quarantined_ratio"))
    drift_flag = bool(drift.get("worsening")) if isinstance(drift, dict) else False
    if (ssi_mean >= 0.6 and quarantined_ratio >= 0.4) and drift_flag:
        severity = min(1.0, (ssi_mean * 0.6 + quarantined_ratio * 0.4))
        gap_id = _sha(f"{run_id}:{ts}:integrity:{ssi_mean}:{quarantined_ratio}")[:16]
        gaps.append(
            DataGap(
                gap_id=gap_id,
                kind=GapKind.INTEGRITY_GAP,
                topic_key=integrity.get("topic_key"),
                horizon=integrity.get("horizon") or "H90D",
                domain=integrity.get("domain") or "INTEGRITY",
                component_ids=list(components.get("top_components", []))[:10],
                portfolio_ids=list(integrity.get("portfolio_ids", ["short_term_core"])),
                symptoms={
                    "ssi_mean": ssi_mean,
                    "quarantined_ratio": quarantined_ratio,
                    "drift_worsening": drift_flag,
                },
                evidence=[
                    {
                        "artifact": inputs.integrity_snapshot_path,
                        "keys": ["ssi_mean", "quarantined_ratio"],
                    }
                ],
                priority=float(0.65 + 0.35 * severity),
                created_ts=ts,
                provenance={"run_id": run_id, "detector": "dap_builder.v0.1"},
            )
        )

    unknown_rate = _safe_float(components.get("unknown_rate"))
    unknown_target = 0.35
    if unknown_rate and unknown_rate > unknown_target:
        severity = min(1.0, (unknown_rate - unknown_target) / (1.0 - unknown_target))
        gap_id = _sha(f"{run_id}:{ts}:struct:{unknown_rate}")[:16]
        gaps.append(
            DataGap(
                gap_id=gap_id,
                kind=GapKind.STRUCTURAL_GAP,
                topic_key=components.get("topic_key"),
                horizon=components.get("horizon") or "H5Y",
                domain=components.get("domain") or "FORECAST",
                component_ids=list(components.get("missing_components", []))[:20],
                portfolio_ids=list(components.get("portfolio_ids", ["long_horizon_integrity"])),
                symptoms={"unknown_rate": unknown_rate, "target": unknown_target},
                evidence=[{"artifact": inputs.component_scores_path, "key": "unknown_rate"}],
                priority=float(0.55 + 0.45 * severity),
                created_ts=ts,
                provenance={"run_id": run_id, "detector": "dap_builder.v0.1"},
            )
        )

    gaps.sort(key=lambda gap: (-gap.priority, gap.kind.value, gap.gap_id))
    return gaps[:10]


def _make_action_id(run_id: str, gap_id: str, idx: int, kind: str) -> str:
    return _sha(f"{run_id}:{gap_id}:{idx}:{kind}")[:16]


def actions_for_gaps(
    run_id: str,
    ts: str,
    gaps: List[DataGap],
    playbook_path: str,
) -> List[AcquisitionAction]:
    playbook = load_playbook_yaml(playbook_path)
    rules = validate_playbook(playbook)

    actions: List[AcquisitionAction] = []
    for gap in gaps:
        gap_dict = {"kind": gap.kind.value, "horizon": gap.horizon, "domain": gap.domain}
        matched: List[Dict[str, Any]] = []
        for rule in rules:
            if rule_matches(rule, gap_dict):
                matched = rule.recommend
                break
        if not matched:
            continue

        for idx, rec in enumerate(matched[:2]):
            kind = rec.get("kind")
            method = rec.get("method", "unknown")
            selector = rec.get("selector", {}) if isinstance(rec.get("selector", {}), dict) else {}
            cadence_hint = rec.get("cadence_hint")
            expected_template = (
                rec.get("expected_impact_template", {})
                if isinstance(rec.get("expected_impact_template", {}), dict)
                else {}
            )

            if kind not in ("ONLINE_FETCH", "OFFLINE_REQUEST"):
                continue

            action_kind = (
                AcquisitionActionKind.ONLINE_FETCH
                if kind == "ONLINE_FETCH"
                else AcquisitionActionKind.OFFLINE_REQUEST
            )
            action_id = _make_action_id(run_id, gap.gap_id, idx, kind)
            cost = estimate_cost(kind, cadence_hint)
            risk = estimate_risk(gap.kind.value, kind)

            if action_kind == AcquisitionActionKind.ONLINE_FETCH:
                nodes = selector.get("vector_node_ids", [])
                instructions = f"Fetch allowlisted sources for vector nodes: {nodes}. Transport: OSH→Decodo."
            else:
                instructions = (
                    f"Offline acquisition required: {json.dumps(selector, ensure_ascii=False)}"
                )

            actions.append(
                AcquisitionAction(
                    action_id=action_id,
                    kind=action_kind,
                    topic_key=gap.topic_key,
                    horizon=gap.horizon,
                    method=method,
                    selector=selector,
                    cadence_hint=cadence_hint,
                    expected_impact=expected_template,
                    cost_estimate=cost,
                    risk_estimate=risk,
                    instructions=instructions,
                    provenance={
                        "run_id": run_id,
                        "gap_id": gap.gap_id,
                        "playbook": os.path.basename(playbook_path),
                    },
                )
            )

    actions.sort(key=lambda action: (action.kind.value, action.method, action.action_id))
    return actions[:20]


def build_dap(
    run_id: str,
    out_dir: str,
    playbook_path: str,
    inputs: DapInputs,
    ts: Optional[str] = None,
) -> Tuple[str, str]:
    ts = ts or _utc_now_iso()
    gaps = detect_gaps(run_id, ts, inputs)
    actions = actions_for_gaps(run_id, ts, gaps, playbook_path)

    plan_id = _sha(f"{run_id}:{ts}:{len(gaps)}:{len(actions)}")[:16]
    plan = DataAcquisitionPlan(
        plan_id=plan_id,
        ts=ts,
        run_id=run_id,
        gaps=gaps,
        actions=actions,
        summary={
            "gap_count": len(gaps),
            "action_count": len(actions),
            "top_gap_kinds": [gap.kind.value for gap in gaps[:3]],
        },
        provenance={
            "run_id": run_id,
            "builder": "dap_builder.v0.1",
            "inputs": {
                "forecast_scores_path": inputs.forecast_scores_path,
                "regime_scores_path": inputs.regime_scores_path,
                "component_scores_path": inputs.component_scores_path,
                "drift_report_path": inputs.drift_report_path,
                "smv_report_path": inputs.smv_report_path,
                "integrity_snapshot_path": inputs.integrity_snapshot_path,
            },
        },
    )

    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, f"dap_{run_id}.json")
    md_path = os.path.join(out_dir, f"dap_{run_id}.md")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(plan.to_dict(), f, ensure_ascii=False, indent=2)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Data Acquisition Plan (DAP) v0.1\n\n")
        f.write(f"- run_id: `{run_id}`\n- ts: `{ts}`\n- plan_id: `{plan_id}`\n\n")
        f.write("## Top gaps\n")
        for gap in gaps[:5]:
            f.write(
                f"- **{gap.kind.value}** horizon={gap.horizon} domain={gap.domain} priority={gap.priority:.2f} symptoms={gap.symptoms}\n"
            )
        f.write("\n## Actions\n")
        for action in actions:
            f.write(
                f"- **{action.kind.value}** method={action.method} cadence={action.cadence_hint} selector={action.selector}\n"
            )
            f.write(
                f"  - impact={action.expected_impact} cost={action.cost_estimate} risk={action.risk_estimate}\n"
            )
            f.write(f"  - instructions: {action.instructions}\n")
        f.write("\n## Provenance\n")
        f.write(json.dumps(plan.provenance, ensure_ascii=False, indent=2))
        f.write("\n")

    return json_path, md_path
