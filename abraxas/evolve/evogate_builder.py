from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .evogate_types import EvoGateReport, ReplayResult
from .replay_adapter import metric_deltas, run_replay_command


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else None


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def _select_proposals(epp: Dict[str, Any], max_apply: int = 8) -> List[Dict[str, Any]]:
    """
    Deterministic selection:
      - Prefer OFFLINE_EVIDENCE_ESCALATION (safe)
      - Prefer cadence changes over SIW loosen/tighten
      - Then SIW tighten (risk-reducing)
      - Finally SIW loosen (riskier)
    """
    props = epp.get("proposals", []) or []
    if not isinstance(props, list):
        return []

    def pri(k: str) -> int:
        if k == "OFFLINE_EVIDENCE_ESCALATION":
            return 0
        if k == "VECTOR_NODE_CADENCE_CHANGE":
            return 1
        if k == "SIW_TIGHTEN_SOURCE":
            return 2
        if k == "COMPONENT_FOCUS_SUGGESTION":
            return 3
        if k == "SIW_LOOSEN_SOURCE":
            return 4
        return 9

    props_sorted = sorted(
        props, key=lambda p: (pri(str(p.get("kind"))), str(p.get("proposal_id")))
    )
    return props_sorted[:max_apply]


def _apply_to_candidate_policy(
    selected: List[Dict[str, Any]],
    base_policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    v0.1 policy format: a generic JSON policy overlay.
    Later: write adapters that transform into your SIW/vector-map YAMLs.
    """
    base = dict(base_policy or {})
    overlay = base.get("overlay", {})
    if not isinstance(overlay, dict):
        overlay = {}

    intents: Dict[str, Any] = overlay.get("intents", {})
    if not isinstance(intents, dict):
        intents = {}

    for proposal in selected:
        proposal_id = str(proposal.get("proposal_id"))
        intents[proposal_id] = {
            "kind": proposal.get("kind"),
            "target": proposal.get("target"),
            "recommended_change": proposal.get("recommended_change"),
            "expected_impact": proposal.get("expected_impact"),
            "risk": proposal.get("risk"),
            "confidence": proposal.get("confidence"),
        }

    overlay["intents"] = intents
    base["overlay"] = overlay
    base.setdefault("version", "candidate_policy.v0.1")
    return base


def _load_baseline_metrics(path: Optional[str]) -> Dict[str, float]:
    """
    Minimal baseline loader.
    Accepts {"metrics":{"brier":0.12,"calibration_error":0.08}} or {"brier":...}
    """
    data = _read_json(path) or {}
    if "metrics" in data and isinstance(data["metrics"], dict):
        return {
            k: float(v)
            for k, v in data["metrics"].items()
            if isinstance(v, (int, float))
        }
    return {k: float(v) for k, v in data.items() if isinstance(v, (int, float))}


def _replay_real_or_stub(
    *,
    run_id: str,
    selected: List[Dict[str, Any]],
    baseline_policy_path: Optional[str],
    candidate_policy_path: str,
    replay_inputs_dir: Optional[str],
    replay_cmd: Optional[str],
    baseline_metrics_path: Optional[str],
) -> ReplayResult:
    """
    Prefer real replay via command adapter; fall back to stub if command is missing.
    """
    if replay_cmd or os.getenv("ABRAXAS_REPLAY_CMD", "").strip():
        base_out = os.path.join(os.path.dirname(candidate_policy_path), "baseline_metrics.json")
        cand_out = os.path.join(os.path.dirname(candidate_policy_path), "candidate_metrics.json")

        base_policy = baseline_policy_path or candidate_policy_path
        base_run = run_replay_command(
            run_id=run_id,
            policy_path=base_policy,
            out_metrics_path=base_out,
            inputs_dir=replay_inputs_dir,
            replay_cmd=replay_cmd,
        )
        cand_run = run_replay_command(
            run_id=run_id,
            policy_path=candidate_policy_path,
            out_metrics_path=cand_out,
            inputs_dir=replay_inputs_dir,
            replay_cmd=replay_cmd,
        )
        ok = bool(base_run.ok and cand_run.ok)
        deltas = metric_deltas(base_run.metrics, cand_run.metrics) if ok else {}
        notes: List[str] = []
        if not ok:
            notes.append("real_replay_failed")
        return ReplayResult(
            ok=ok,
            metric_deltas=deltas,
            notes=notes,
            provenance={
                "method": "command",
                "baseline_metrics": base_out,
                "candidate_metrics": cand_out,
                "baseline_exit": base_run.exit_code,
                "candidate_exit": cand_run.exit_code,
            },
        )

    notes = ["replay_stub_v0.1"]
    delta_brier = 0.0
    delta_cal = 0.0
    for proposal in selected:
        kind = str(proposal.get("kind"))
        if kind == "OFFLINE_EVIDENCE_ESCALATION":
            delta_brier -= 0.0005
        elif kind == "VECTOR_NODE_CADENCE_CHANGE":
            delta_brier -= 0.0003
        elif kind == "SIW_TIGHTEN_SOURCE":
            delta_cal -= 0.0004
        elif kind == "SIW_LOOSEN_SOURCE":
            delta_brier += 0.0002
    return ReplayResult(
        ok=True,
        metric_deltas={
            "brier": float(delta_brier),
            "calibration_error": float(delta_cal),
        },
        notes=notes,
        provenance={
            "method": "stub",
            "warning": "Set ABRAXAS_REPLAY_CMD to enable real replay.",
        },
    )


def build_evogate(
    run_id: str,
    out_reports_dir: str,
    staging_root_dir: str,
    epp_path: str,
    base_policy_path: Optional[str] = None,
    baseline_metrics_path: Optional[str] = None,
    replay_inputs_dir: Optional[str] = None,
    replay_cmd: Optional[str] = None,
    thresholds: Optional[Dict[str, Any]] = None,
    ts: Optional[str] = None,
) -> Tuple[str, str, Dict[str, Any]]:
    ts = ts or _utc_now_iso()
    thresholds = thresholds or {
        "brier_max_delta": 0.0,
        "calibration_error_max_delta": 0.0,
    }

    epp = _read_json(epp_path)
    if not epp:
        raise ValueError(f"Missing or invalid EPP JSON: {epp_path}")

    pack_id = str(epp.get("pack_id") or "unknown_pack")
    selected = _select_proposals(epp)
    applied_ids = [str(proposal.get("proposal_id")) for proposal in selected]

    base_policy = _read_json(base_policy_path) if base_policy_path else None
    candidate = _apply_to_candidate_policy(selected, base_policy=base_policy)

    candidate_dir = os.path.join(staging_root_dir, run_id)
    candidate_policy_path = os.path.join(candidate_dir, "candidate_policy.json")
    _write_json(candidate_policy_path, candidate)

    _ = _load_baseline_metrics(baseline_metrics_path)
    replay = _replay_real_or_stub(
        run_id=run_id,
        selected=selected,
        baseline_policy_path=base_policy_path,
        candidate_policy_path=candidate_policy_path,
        replay_inputs_dir=replay_inputs_dir,
        replay_cmd=replay_cmd,
        baseline_metrics_path=baseline_metrics_path,
    )

    brier_ok = replay.metric_deltas.get("brier", 0.0) <= float(
        thresholds.get("brier_max_delta", 0.0)
    )
    cal_ok = replay.metric_deltas.get("calibration_error", 0.0) <= float(
        thresholds.get("calibration_error_max_delta", 0.0)
    )
    promote = bool(replay.ok and brier_ok and cal_ok)

    notes: List[str] = []
    if "warning" in replay.provenance:
        notes.append("replay_is_stub")

    report = EvoGateReport(
        run_id=run_id,
        ts=ts,
        pack_id=pack_id,
        applied_proposal_ids=applied_ids,
        candidate_policy_path=candidate_policy_path,
        baseline_metrics_path=baseline_metrics_path,
        replay=replay,
        promote_recommended=promote,
        thresholds=thresholds,
        notes=notes,
        provenance={
            "builder": "evogate_builder.v0.1",
            "inputs": {
                "epp": epp_path,
                "base_policy": base_policy_path,
                "baseline_metrics": baseline_metrics_path,
            },
        },
    )

    os.makedirs(out_reports_dir, exist_ok=True)
    json_path = os.path.join(out_reports_dir, f"evogate_{run_id}.json")
    md_path = os.path.join(out_reports_dir, f"evogate_{run_id}.md")
    _write_json(json_path, report.to_dict())

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# EvoGate v0.1 — Staging Apply + Replay Gate\n\n")
        f.write(f"- run_id: `{run_id}`\n- ts: `{ts}`\n- epp pack: `{pack_id}`\n")
        f.write(f"- candidate_policy: `{candidate_policy_path}`\n\n")
        f.write("## Applied proposals\n")
        for proposal_id in applied_ids:
            f.write(f"- `{proposal_id}`\n")
        f.write("\n## Replay deltas (estimated)\n")
        f.write(json.dumps(replay.metric_deltas, ensure_ascii=False, indent=2))
        f.write("\n\n## Promote recommended\n")
        f.write(f"- **{promote}**\n")
        if notes:
            f.write("\n## Notes\n")
            for note in notes:
                f.write(f"- {note}\n")

    meta = {"applied": len(applied_ids), "promote": promote, "notes": notes}
    return json_path, md_path, meta
