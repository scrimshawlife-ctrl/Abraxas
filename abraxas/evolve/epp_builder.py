from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from abraxas.core.provenance import hash_canonical_json

from .ledger import append_epp_ledger
from .types import EvolutionProposal, EvolutionProposalPack, ProposalKind


@dataclass(frozen=True)
class _ArtifactRef:
    path: str
    payload: Dict[str, Any]


def build_epp(
    run_id: str,
    out_dir: str = "out/reports",
    inputs_dir: str = "out/reports",
    osh_ledger_path: str = "out/osh_ledgers/fetch_artifacts.jsonl",
    integrity_snapshot_path: Optional[str] = None,
    dap_path: Optional[str] = None,
    mwr_path: Optional[str] = None,
    a2_path: Optional[str] = None,
    a2_phase_path: Optional[str] = None,
    audit_path: Optional[str] = None,
    ledger_path: str = "out/value_ledgers/epp_runs.jsonl",
    max_proposals: int = 25,
    ts: Optional[str] = None,
) -> Tuple[str, str]:
    ts = ts or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    inputs_dir_path = Path(inputs_dir)
    out_dir_path = Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    smv_reports = _load_reports(inputs_dir_path, f"smv_{run_id}_*.json")
    cre_reports = _load_reports(inputs_dir_path, f"cre_{run_id}_*.json")
    if not cre_reports:
        cre_reports = _load_reports(inputs_dir_path, f"counterfactual_{run_id}_*.json")

    dap_path = dap_path or str(inputs_dir_path / f"dap_{run_id}.json")
    dap = _read_json_if_exists(dap_path)

    integrity_snapshot = None
    integrity_path = integrity_snapshot_path
    if integrity_path is None:
        integrity_candidates = sorted(inputs_dir_path.glob(f"integrity_snapshot_{run_id}*.json"))
        if integrity_candidates:
            integrity_path = str(integrity_candidates[0])
    integrity_snapshot = _read_json_if_exists(integrity_path) if integrity_path else None

    osh_stats = _load_osh_stats(osh_ledger_path)

    unit_records = _collect_unit_records(smv_reports)
    smv_range = _smv_range(unit_records)

    cre_sensitivity = _collect_cre_sensitivity(cre_reports)
    sensitivity_range = _range_from_values(list(cre_sensitivity.values()))

    risk_components = _risk_components(integrity_snapshot, osh_stats)
    proposals = _build_proposals(
        unit_records=unit_records,
        smv_range=smv_range,
        cre_sensitivity=cre_sensitivity,
        sensitivity_range=sensitivity_range,
        risk_components=risk_components,
        smv_reports=smv_reports,
        cre_reports=cre_reports,
        dap=dap,
        osh_stats=osh_stats,
        osh_ledger_path=osh_ledger_path,
        integrity_path=integrity_path,
    )

    mwr_path = mwr_path or str(inputs_dir_path / f"mwr_{run_id}.json")
    a2_path = a2_path or str(inputs_dir_path / f"a2_{run_id}.json")
    mwr = _read_json_if_exists(mwr_path)
    a2 = _read_json_if_exists(a2_path)
    proposals.extend(
        _proposals_from_mwr_a2(
            run_id=run_id,
            mwr=mwr,
            a2=a2,
            mwr_path=mwr_path if mwr else None,
            a2_path=a2_path if a2 else None,
        )
    )

    a2_phase_path = a2_phase_path or str(inputs_dir_path / f"a2_phase_{run_id}.json")
    a2_phase = _read_json_if_exists(a2_phase_path)
    proposals.extend(
        _proposals_from_a2_phase(
            run_id=run_id,
            a2_phase=a2_phase,
            a2_phase_path=a2_phase_path if a2_phase else None,
        )
    )

    forecast_score_path = str(inputs_dir_path / f"forecast_score_{run_id}.json")
    forecast_score = _read_json_if_exists(forecast_score_path)
    proposals.extend(
        _proposals_from_gate(
            run_id=run_id,
            gate=forecast_score.get("gate") if isinstance(forecast_score, dict) else None,
            forecast_score_path=forecast_score_path if forecast_score else None,
        )
    )

    audit = _read_audit(audit_path)
    proposals.extend(
        _proposals_from_audit(
            run_id=run_id,
            audit=audit,
            audit_path=audit_path if audit else None,
        )
    )

    proposals = sorted(
        proposals,
        key=lambda p: (
            -float(p.rationale.get("score", 0.0)),
            p.kind.value,
            p.proposal_id,
        ),
    )
    proposals = proposals[:max_proposals]

    summary = _summarize(proposals, osh_stats)
    pack_payload = {
        "run_id": run_id,
        "ts": ts,
        "proposals": [proposal.to_dict() for proposal in proposals],
        "summary": summary,
    }
    pack_id = f"epp_{hash_canonical_json(pack_payload)[:16]}"

    pack = EvolutionProposalPack(
        pack_id=pack_id,
        run_id=run_id,
        ts=ts,
        proposals=proposals,
        summary=summary,
        provenance={
            "smv_reports": [ref.path for ref in smv_reports],
            "cre_reports": [ref.path for ref in cre_reports],
            "dap_path": dap_path if dap else None,
            "osh_ledger_path": osh_ledger_path,
            "integrity_snapshot_path": integrity_path,
            "mwr_path": mwr_path if mwr else None,
            "a2_path": a2_path if a2 else None,
            "a2_phase_path": a2_phase_path if a2_phase else None,
            "forecast_score_path": forecast_score_path if forecast_score else None,
            "audit_path": audit_path if audit else None,
        },
    )

    json_path = out_dir_path / f"epp_{run_id}.json"
    md_path = out_dir_path / f"epp_{run_id}.md"
    json_path.write_text(json.dumps(pack.to_dict(), indent=2, sort_keys=True))
    md_path.write_text(_render_md(pack))

    append_epp_ledger(pack.to_dict(), ledger_path=ledger_path)

    return str(json_path), str(md_path)


def _load_reports(base_dir: Path, pattern: str) -> List[_ArtifactRef]:
    reports: List[_ArtifactRef] = []
    for path in sorted(base_dir.glob(pattern)):
        payload = _read_json_if_exists(str(path))
        if payload is None:
            continue
        reports.append(_ArtifactRef(path=str(path), payload=payload))
    return reports


def _read_json_if_exists(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return None
    return data


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(entry, dict):
                entries.append(entry)
    return entries


def _read_audit(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    if path.endswith(".jsonl"):
        entries = _read_jsonl(path)
        for entry in reversed(entries):
            if isinstance(entry, dict):
                return entry
        return None
    return _read_json_if_exists(path)


def _collect_unit_records(smv_reports: Iterable[_ArtifactRef]) -> Dict[str, Dict[str, Any]]:
    records: Dict[str, Dict[str, Any]] = {}
    for report in smv_reports:
        units = report.payload.get("units", [])
        for unit in units:
            unit_id = unit.get("unit_id")
            if not unit_id:
                continue
            record = records.setdefault(
                unit_id,
                {
                    "unit_id": unit_id,
                    "portfolio_id": report.payload.get("portfolio_id"),
                    "smv_overall": unit.get("smv_overall"),
                    "source": report.path,
                },
            )
            if record.get("smv_overall") is None:
                record["smv_overall"] = unit.get("smv_overall")
    return records


def _smv_range(records: Dict[str, Dict[str, Any]]) -> Tuple[float, float]:
    values = [float(r.get("smv_overall")) for r in records.values() if r.get("smv_overall") is not None]
    if not values:
        return 0.0, 0.0
    return min(values), max(values)


def _collect_cre_sensitivity(cre_reports: Iterable[_ArtifactRef]) -> Dict[str, float]:
    sensitivity: Dict[str, float] = {}
    for report in cre_reports:
        extracted = _extract_cre_sensitivity(report.payload)
        for unit_id, value in extracted.items():
            sensitivity[unit_id] = max(sensitivity.get(unit_id, 0.0), value)
    return sensitivity


def _extract_cre_sensitivity(report: Dict[str, Any]) -> Dict[str, float]:
    if "unit_sensitivity" in report and isinstance(report["unit_sensitivity"], list):
        out: Dict[str, float] = {}
        for entry in report["unit_sensitivity"]:
            unit_id = entry.get("unit_id")
            magnitude = entry.get("delta_magnitude")
            if unit_id and isinstance(magnitude, (int, float)):
                out[unit_id] = float(abs(magnitude))
        return out

    delta_summary = report.get("delta_summary", {})
    score_deltas = delta_summary.get("score_deltas", {})
    component_scores = score_deltas.get("component_scores", {})
    out = {}
    if isinstance(component_scores, dict):
        for component_id, deltas in component_scores.items():
            if not isinstance(deltas, dict):
                continue
            magnitude = 0.0
            for value in deltas.values():
                if isinstance(value, (int, float)):
                    magnitude += abs(float(value))
            out[component_id] = magnitude
    return out


def _range_from_values(values: List[float]) -> Tuple[float, float]:
    if not values:
        return 0.0, 0.0
    return min(values), max(values)


def _risk_components(
    integrity_snapshot: Optional[Dict[str, Any]],
    osh_stats: Dict[str, float],
) -> Dict[str, float]:
    ssi = float(integrity_snapshot.get("ssi_mean", 0.0)) if integrity_snapshot else 0.0
    quarantine = float(integrity_snapshot.get("quarantined_ratio", 0.0)) if integrity_snapshot else 0.0
    transport_fail = float(osh_stats.get("failure_rate", 0.0))
    risk = _clamp(ssi + quarantine + transport_fail)
    return {
        "ssi_exposure": _clamp(ssi),
        "quarantine_likelihood": _clamp(quarantine),
        "transport_failure": _clamp(transport_fail),
        "composite": risk,
    }


def _load_osh_stats(ledger_path: str) -> Dict[str, float]:
    entries = _read_jsonl(ledger_path)
    total = 0
    ok = 0
    offline = 0
    for entry in entries:
        status = entry.get("status")
        if status not in ("ok", "offline_required"):
            continue
        total += 1
        if status == "ok":
            ok += 1
        else:
            offline += 1
    failure_rate = (offline / total) if total else 0.0
    return {
        "total": float(total),
        "ok": float(ok),
        "offline_required": float(offline),
        "failure_rate": failure_rate,
    }


def _build_proposals(
    *,
    unit_records: Dict[str, Dict[str, Any]],
    smv_range: Tuple[float, float],
    cre_sensitivity: Dict[str, float],
    sensitivity_range: Tuple[float, float],
    risk_components: Dict[str, float],
    smv_reports: List[_ArtifactRef],
    cre_reports: List[_ArtifactRef],
    dap: Optional[Dict[str, Any]],
    osh_stats: Dict[str, float],
    osh_ledger_path: str,
    integrity_path: Optional[str],
) -> List[EvolutionProposal]:
    proposals: List[EvolutionProposal] = []
    min_smv, max_smv = smv_range
    min_sens, max_sens = sensitivity_range
    benefit_threshold_low = 0.3
    benefit_threshold_high = 0.7
    sensitivity_threshold_high = 0.7
    risk_high = 0.6
    risk_very_high = 0.8
    transport_fail = float(risk_components.get("transport_failure", 0.0))

    for unit_id, record in unit_records.items():
        smv_value = record.get("smv_overall")
        if smv_value is None:
            continue
        smv_value = float(smv_value)
        benefit = _normalize(smv_value, min_smv, max_smv)
        sensitivity_raw = cre_sensitivity.get(unit_id, 0.0)
        sensitivity = _normalize(sensitivity_raw, min_sens, max_sens)
        risk = float(risk_components.get("composite", 0.0))
        confidence = _clamp(1.0 - risk)

        rationale = {
            "smv_overall": smv_value,
            "benefit": benefit,
            "sensitivity": sensitivity,
            "risk": risk,
            "transport_failure_rate": transport_fail,
        }
        score = benefit + sensitivity - risk
        rationale["score"] = score

        if (smv_value < 0 and risk >= risk_high) or (benefit <= benefit_threshold_low and risk >= risk_very_high):
            proposals.append(
                _proposal_for_unit(
                    unit_id=unit_id,
                    kind=ProposalKind.SIW_TIGHTEN_SOURCE,
                    record=record,
                    rationale=rationale,
                    risk_components=risk_components,
                    recommended_change={
                        "siw_max": round(max(0.2, 1.0 - risk), 2),
                        "direction": "tighten",
                    },
                    expected_impact={
                        "smv_overall": smv_value,
                        "risk": risk,
                    },
                    confidence=confidence,
                    smv_reports=smv_reports,
                    cre_reports=cre_reports,
                    dap=dap,
                    osh_stats=osh_stats,
                    osh_ledger_path=osh_ledger_path,
                    integrity_path=integrity_path,
                )
            )

        if benefit >= benefit_threshold_high and risk <= (1.0 - benefit_threshold_high):
            proposals.append(
                _proposal_for_unit(
                    unit_id=unit_id,
                    kind=ProposalKind.SIW_LOOSEN_SOURCE,
                    record=record,
                    rationale=rationale,
                    risk_components=risk_components,
                    recommended_change={
                        "siw_min": round(min(0.9, benefit), 2),
                        "direction": "loosen",
                    },
                    expected_impact={
                        "smv_overall": smv_value,
                        "benefit": benefit,
                    },
                    confidence=confidence,
                    smv_reports=smv_reports,
                    cre_reports=cre_reports,
                    dap=dap,
                    osh_stats=osh_stats,
                    osh_ledger_path=osh_ledger_path,
                    integrity_path=integrity_path,
                )
            )

        if benefit >= benefit_threshold_high and sensitivity >= sensitivity_threshold_high and transport_fail <= 0.2:
            proposals.append(
                _proposal_for_unit(
                    unit_id=unit_id,
                    kind=ProposalKind.VECTOR_NODE_CADENCE_CHANGE,
                    record=record,
                    rationale=rationale,
                    risk_components=risk_components,
                    recommended_change={
                        "cadence": "daily",
                        "direction": "increase",
                    },
                    expected_impact={
                        "sensitivity": sensitivity,
                        "benefit": benefit,
                    },
                    confidence=confidence,
                    smv_reports=smv_reports,
                    cre_reports=cre_reports,
                    dap=dap,
                    osh_stats=osh_stats,
                    osh_ledger_path=osh_ledger_path,
                    integrity_path=integrity_path,
                )
            )
        elif benefit <= benefit_threshold_low or transport_fail >= 0.4:
            proposals.append(
                _proposal_for_unit(
                    unit_id=unit_id,
                    kind=ProposalKind.VECTOR_NODE_CADENCE_CHANGE,
                    record=record,
                    rationale=rationale,
                    risk_components=risk_components,
                    recommended_change={
                        "cadence": "weekly",
                        "direction": "decrease",
                    },
                    expected_impact={
                        "sensitivity": sensitivity,
                        "benefit": benefit,
                    },
                    confidence=confidence,
                    smv_reports=smv_reports,
                    cre_reports=cre_reports,
                    dap=dap,
                    osh_stats=osh_stats,
                    osh_ledger_path=osh_ledger_path,
                    integrity_path=integrity_path,
                )
            )

    proposals.extend(_offline_escalations(dap, osh_stats, risk_components, integrity_path))
    proposals.extend(_component_focus(dap, risk_components, integrity_path))

    return proposals


def _proposal_for_unit(
    *,
    unit_id: str,
    kind: ProposalKind,
    record: Dict[str, Any],
    rationale: Dict[str, Any],
    risk_components: Dict[str, float],
    recommended_change: Dict[str, Any],
    expected_impact: Dict[str, Any],
    confidence: float,
    smv_reports: List[_ArtifactRef],
    cre_reports: List[_ArtifactRef],
    dap: Optional[Dict[str, Any]],
    osh_stats: Dict[str, float],
    osh_ledger_path: str,
    integrity_path: Optional[str],
) -> EvolutionProposal:
    target = {
        "unit_id": unit_id,
        "unit_kind": "smv_unit",
        "vector_node_id": None,
        "allowlist_source_id": None,
    }
    payload = {
        "kind": kind.value,
        "target": target,
        "recommended_change": recommended_change,
        "rationale": rationale,
    }
    proposal_id = f"epp_{hash_canonical_json(payload)[:16]}"
    return EvolutionProposal(
        proposal_id=proposal_id,
        kind=kind,
        target=target,
        rationale=rationale,
        recommended_change=recommended_change,
        expected_impact=expected_impact,
        risk=risk_components,
        confidence=confidence,
        provenance={
            "smv_report": record.get("source"),
            "cre_reports": [ref.path for ref in cre_reports],
            "dap_plan_id": dap.get("plan_id") if dap else None,
            "osh_ledger_path": osh_ledger_path,
            "integrity_snapshot_path": integrity_path,
        },
    )


def _offline_escalations(
    dap: Optional[Dict[str, Any]],
    osh_stats: Dict[str, float],
    risk_components: Dict[str, float],
    integrity_path: Optional[str],
) -> List[EvolutionProposal]:
    if not dap:
        return []
    offline_required = osh_stats.get("offline_required", 0.0)
    if offline_required < 2:
        return []

    proposals: List[EvolutionProposal] = []
    gaps = dap.get("gaps", []) if isinstance(dap.get("gaps"), list) else []
    critical_gaps = [gap for gap in gaps if float(gap.get("priority", 0.0)) >= 0.75]

    for gap in critical_gaps:
        gap_id = gap.get("gap_id")
        if not gap_id:
            continue
        rationale = {
            "gap_priority": gap.get("priority"),
            "offline_required": offline_required,
            "risk": risk_components.get("composite"),
            "score": float(gap.get("priority", 0.0)) - float(risk_components.get("composite", 0.0)),
        }
        target = {
            "unit_id": gap_id,
            "unit_kind": "gap",
            "vector_node_id": None,
            "allowlist_source_id": None,
        }
        recommended_change = {
            "request_evidence_pack": True,
            "reason": "offline_required_repeated",
        }
        payload = {
            "kind": ProposalKind.OFFLINE_EVIDENCE_ESCALATION.value,
            "target": target,
            "recommended_change": recommended_change,
            "rationale": rationale,
        }
        proposal_id = f"epp_{hash_canonical_json(payload)[:16]}"
        proposals.append(
            EvolutionProposal(
                proposal_id=proposal_id,
                kind=ProposalKind.OFFLINE_EVIDENCE_ESCALATION,
                target=target,
                rationale=rationale,
                recommended_change=recommended_change,
                expected_impact={
                    "offline_required": offline_required,
                    "gap_priority": gap.get("priority"),
                },
                risk=risk_components,
                confidence=_clamp(1.0 - float(risk_components.get("composite", 0.0))),
                provenance={
                    "dap_gap_id": gap_id,
                    "dap_plan_id": dap.get("plan_id"),
                    "integrity_snapshot_path": integrity_path,
                },
            )
        )

    return proposals


def _component_focus(
    dap: Optional[Dict[str, Any]],
    risk_components: Dict[str, float],
    integrity_path: Optional[str],
) -> List[EvolutionProposal]:
    if not dap:
        return []
    gaps = dap.get("gaps", []) if isinstance(dap.get("gaps"), list) else []
    proposals: List[EvolutionProposal] = []
    for gap in gaps:
        if gap.get("kind") != "STRUCTURAL_GAP":
            continue
        gap_id = gap.get("gap_id")
        if not gap_id:
            continue
        unknown_rate = gap.get("symptoms", {}).get("unknown_rate")
        if unknown_rate is not None and float(unknown_rate) < 0.35:
            continue
        rationale = {
            "unknown_rate": unknown_rate,
            "gap_priority": gap.get("priority"),
            "score": float(gap.get("priority", 0.0)) - float(risk_components.get("composite", 0.0)),
        }
        target = {
            "unit_id": gap_id,
            "unit_kind": "gap",
            "vector_node_id": None,
            "allowlist_source_id": None,
        }
        recommended_change = {
            "action": "focus_components",
            "missing_components": gap.get("component_ids", [])[:5],
        }
        payload = {
            "kind": ProposalKind.COMPONENT_FOCUS_SUGGESTION.value,
            "target": target,
            "recommended_change": recommended_change,
            "rationale": rationale,
        }
        proposal_id = f"epp_{hash_canonical_json(payload)[:16]}"
        proposals.append(
            EvolutionProposal(
                proposal_id=proposal_id,
                kind=ProposalKind.COMPONENT_FOCUS_SUGGESTION,
                target=target,
                rationale=rationale,
                recommended_change=recommended_change,
                expected_impact={
                    "unknown_rate": unknown_rate,
                    "gap_priority": gap.get("priority"),
                },
                risk=risk_components,
                confidence=_clamp(1.0 - float(risk_components.get("composite", 0.0))),
                provenance={
                    "dap_gap_id": gap_id,
                    "dap_plan_id": dap.get("plan_id"),
                    "integrity_snapshot_path": integrity_path,
                },
            )
        )
    return proposals


def _normalize(value: float, min_value: float, max_value: float) -> float:
    if max_value <= min_value:
        return 0.5
    return _clamp((value - min_value) / (max_value - min_value))


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _summarize(proposals: List[EvolutionProposal], osh_stats: Dict[str, float]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "proposal_count": len(proposals),
        "by_kind": {},
        "transport": osh_stats,
    }
    for proposal in proposals:
        summary["by_kind"].setdefault(proposal.kind.value, 0)
        summary["by_kind"][proposal.kind.value] += 1

    summary["top_tighten_candidates"] = _top_targets(
        proposals, ProposalKind.SIW_TIGHTEN_SOURCE
    )
    summary["top_loosen_candidates"] = _top_targets(
        proposals, ProposalKind.SIW_LOOSEN_SOURCE
    )
    summary["cadence_changes"] = _top_targets(
        proposals, ProposalKind.VECTOR_NODE_CADENCE_CHANGE
    )
    summary["offline_escalations"] = _top_targets(
        proposals, ProposalKind.OFFLINE_EVIDENCE_ESCALATION
    )
    summary["evidence_escalations"] = _top_targets(
        proposals, ProposalKind.EVIDENCE_ESCALATION
    )

    return summary


def _top_targets(
    proposals: List[EvolutionProposal], kind: ProposalKind, limit: int = 5
) -> List[Dict[str, Any]]:
    filtered = [p for p in proposals if p.kind == kind]
    filtered.sort(key=lambda p: (-float(p.rationale.get("score", 0.0)), p.proposal_id))
    out = []
    for proposal in filtered[:limit]:
        out.append(
            {
                "proposal_id": proposal.proposal_id,
                "unit_id": proposal.target.get("unit_id"),
                "score": proposal.rationale.get("score"),
            }
        )
    return out


def _render_md(pack: EvolutionProposalPack) -> str:
    lines = [
        "# Evolution Proposal Pack (EPP)",
        "",
        f"- Pack ID: {pack.pack_id}",
        f"- Run ID: {pack.run_id}",
        f"- Timestamp: {pack.ts}",
        "",
        "## Top tighten candidates",
    ]
    lines.extend(_render_proposal_list(pack, ProposalKind.SIW_TIGHTEN_SOURCE))
    lines.extend(["", "## Top loosen candidates"])
    lines.extend(_render_proposal_list(pack, ProposalKind.SIW_LOOSEN_SOURCE))
    lines.extend(["", "## Cadence changes"])
    lines.extend(_render_proposal_list(pack, ProposalKind.VECTOR_NODE_CADENCE_CHANGE))
    lines.extend(["", "## Offline escalations"])
    lines.extend(_render_proposal_list(pack, ProposalKind.OFFLINE_EVIDENCE_ESCALATION))
    lines.extend(["", "## Evidence escalations"])
    lines.extend(_render_proposal_list(pack, ProposalKind.EVIDENCE_ESCALATION))
    lines.extend(["", "## Component focus suggestions"])
    lines.extend(_render_proposal_list(pack, ProposalKind.COMPONENT_FOCUS_SUGGESTION))
    return "\n".join(lines)


def _render_proposal_list(pack: EvolutionProposalPack, kind: ProposalKind) -> List[str]:
    items = [p for p in pack.proposals if p.kind == kind]
    if not items:
        return ["- None"]
    lines = []
    for proposal in items[:10]:
        unit_id = proposal.target.get("unit_id")
        score = float(proposal.rationale.get("score", 0.0))
        lines.append(f"- {unit_id} ({proposal.proposal_id}) score={score:.3f}")
    return lines


def _proposals_from_mwr_a2(
    *,
    run_id: str,
    mwr: Optional[Dict[str, Any]],
    a2: Optional[Dict[str, Any]],
    mwr_path: Optional[str],
    a2_path: Optional[str],
) -> List[EvolutionProposal]:
    out: List[EvolutionProposal] = []

    def proposal_id(kind: ProposalKind, suffix: str, payload: Dict[str, Any]) -> str:
        base = {"kind": kind.value, "suffix": suffix, "payload": payload}
        return f"epp_{hash_canonical_json(base)[:16]}"

    units = mwr.get("units", []) if isinstance(mwr, dict) else []
    units = units if isinstance(units, list) else []
    front_by_label = {
        str(u.get("label")): u
        for u in units
        if isinstance(u, dict) and u.get("label") is not None
    }

    disinfo = front_by_label.get("disinfo_fog")
    if isinstance(disinfo, dict):
        risk = float((disinfo.get("disinfo_metrics") or {}).get("manipulation_risk_mean", 0.0) or 0.0)
        confidence = float(disinfo.get("confidence", 0.6) or 0.6)
        rationale = {
            "mwr_label": "disinfo_fog",
            "risk": risk,
            "confidence": confidence,
            "score": float(0.6 + 0.2 * confidence + 0.2 * risk),
        }
        target = {"unit_id": "disinfo_fog", "unit_kind": "mwr_front"}
        recommended_change = {
            "user_prompt": (
                "Provide offline evidence pack (screenshots/URLs/archive links) "
                "for claims in disinfo fog before canonizing."
            )
        }
        out.append(
            EvolutionProposal(
                proposal_id=proposal_id(ProposalKind.OFFLINE_EVIDENCE_ESCALATION, "disinfo_fog", target),
                kind=ProposalKind.OFFLINE_EVIDENCE_ESCALATION,
                target=target,
                rationale=rationale,
                recommended_change=recommended_change,
                expected_impact={"metric": "truth_integrity", "delta": 0.02},
                risk={"integrity_risk": max(0.2, risk), "cost_risk": 0.15},
                confidence=max(0.55, min(0.9, 0.6 + 0.2 * confidence)),
                provenance={"mwr_path": mwr_path},
            )
        )

        tighten_target = {"unit_id": "high_risk_claims", "unit_kind": "allowlist_policy"}
        tighten_change = {
            "action": "prefer_primary_sources",
            "note": "During disinfo fog, downrank unverifiable virality.",
        }
        out.append(
            EvolutionProposal(
                proposal_id=proposal_id(ProposalKind.SIW_TIGHTEN_SOURCE, "disinfo_fog", tighten_target),
                kind=ProposalKind.SIW_TIGHTEN_SOURCE,
                target=tighten_target,
                rationale={**rationale, "score": float(0.55 + 0.3 * risk)},
                recommended_change=tighten_change,
                expected_impact={"metric": "manipulation_resilience", "delta": 0.015},
                risk={"coverage_risk": 0.12, "integrity_risk": 0.05},
                confidence=max(0.5, min(0.85, 0.55 + 0.25 * (1.0 - risk))),
                provenance={"mwr_path": mwr_path},
            )
        )

    flash = front_by_label.get("flash_spike")
    if isinstance(flash, dict):
        intensity = float(flash.get("intensity", 0.0) or 0.0)
        confidence = float(flash.get("confidence", 0.6) or 0.6)
        target = {"unit_id": "flash_spike", "unit_kind": "mwr_front"}
        out.append(
            EvolutionProposal(
                proposal_id=proposal_id(ProposalKind.VECTOR_NODE_CADENCE_CHANGE, "flash_spike", target),
                kind=ProposalKind.VECTOR_NODE_CADENCE_CHANGE,
                target=target,
                rationale={
                    "mwr_label": "flash_spike",
                    "intensity": intensity,
                    "score": float(0.5 + 0.4 * intensity),
                },
                recommended_change={"cadence": "fast", "interval_minutes": 90, "ttl_hours": 18},
                expected_impact={"metric": "detection_latency", "delta": -0.10},
                risk={"cost_risk": min(0.35, 0.1 + 0.6 * intensity)},
                confidence=confidence,
                provenance={"mwr_path": mwr_path},
            )
        )

    long_tail = front_by_label.get("long_tail_pressure")
    if isinstance(long_tail, dict):
        confidence = float(long_tail.get("confidence", 0.6) or 0.6)
        target = {"unit_id": "long_tail_pressure", "unit_kind": "mwr_front"}
        out.append(
            EvolutionProposal(
                proposal_id=proposal_id(ProposalKind.VECTOR_NODE_CADENCE_CHANGE, "long_tail", target),
                kind=ProposalKind.VECTOR_NODE_CADENCE_CHANGE,
                target=target,
                rationale={"mwr_label": "long_tail_pressure", "score": 0.45},
                recommended_change={"cadence": "slow", "interval_hours": 18, "ttl_days": 12},
                expected_impact={"metric": "cost", "delta": -0.08},
                risk={"coverage_risk": 0.08},
                confidence=confidence,
                provenance={"mwr_path": mwr_path},
            )
        )

    terms = a2.get("terms", []) if isinstance(a2, dict) else []
    if isinstance(terms, list) and terms:
        scored: List[tuple[float, float, str, Dict[str, Any]]] = []
        for term in terms:
            if not isinstance(term, dict):
                continue
            label = str(term.get("term") or "")
            if not label:
                continue
            novelty = float(term.get("novelty_score", 0.0) or 0.0)
            propagation = float(term.get("propagation_score", 0.0) or 0.0)
            risk = float(term.get("manipulation_risk", 0.0) or 0.0)
            scored.append((-(0.5 * novelty + 0.5 * propagation), risk, label, term))
        scored.sort()
        top = [item[3] for item in scored[:8]]

        target = {"unit_id": "slang_engine", "unit_kind": "component"}
        out.append(
            EvolutionProposal(
                proposal_id=proposal_id(ProposalKind.COMPONENT_FOCUS_SUGGESTION, "a2_terms", target),
                kind=ProposalKind.COMPONENT_FOCUS_SUGGESTION,
                target=target,
                rationale={"a2_terms": len(top), "score": 0.5},
                recommended_change={"watch_terms": [str(t.get("term")) for t in top]},
                expected_impact={"metric": "novelty_capture", "delta": 0.02},
                risk={"cost_risk": 0.06, "integrity_risk": 0.04},
                confidence=0.65,
                provenance={"a2_path": a2_path},
            )
        )

    return out


def _proposals_from_a2_phase(
    *,
    run_id: str,
    a2_phase: Optional[Dict[str, Any]],
    a2_phase_path: Optional[str],
) -> List[EvolutionProposal]:
    if not a2_phase:
        return []
    raw_full = a2_phase.get("raw_full") if isinstance(a2_phase, dict) else None
    profiles = None
    if isinstance(raw_full, dict) and isinstance(raw_full.get("profiles"), list):
        profiles = raw_full.get("profiles")
    if profiles is None:
        profiles = a2_phase.get("profiles", []) if isinstance(a2_phase, dict) else []
    if not isinstance(profiles, list):
        return []

    phase_rank = {
        "surging": 0,
        "resurgent": 1,
        "emergent": 2,
        "plateau": 3,
        "decaying": 4,
        "dormant": 5,
    }
    active_phases = {"surging", "resurgent", "emergent"}
    candidates = [p for p in profiles if isinstance(p, dict)]
    candidates = [p for p in candidates if str(p.get("phase")) in active_phases]
    if not candidates:
        candidates = [p for p in profiles if isinstance(p, dict)]

    scored: List[tuple[int, float, float, str, Dict[str, Any]]] = []
    for profile in candidates:
        term = str(profile.get("term") or profile.get("term_key") or "")
        if not term:
            continue
        phase = str(profile.get("phase") or "")
        v14 = float(profile.get("v14", 0.0) or 0.0)
        v60 = float(profile.get("v60", 0.0) or 0.0)
        risk = float(profile.get("manipulation_risk_mean", 0.0) or 0.0)
        rank = phase_rank.get(phase, 9)
        scored.append((rank, -(v14 + 0.35 * v60), -risk, term, profile))

    if not scored:
        return []
    scored.sort()
    top = scored[:10]
    top_profiles = [item[4] for item in top]
    watch_terms = [str(p.get("term") or p.get("term_key")) for p in top_profiles]
    mean_v14 = sum(float(p.get("v14", 0.0) or 0.0) for p in top_profiles) / max(
        1, len(top_profiles)
    )
    mean_risk = sum(
        float(p.get("manipulation_risk_mean", 0.0) or 0.0) for p in top_profiles
    ) / max(1, len(top_profiles))
    phase_counts: Dict[str, int] = {}
    for profile in top_profiles:
        phase = str(profile.get("phase") or "unknown")
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

    target = {"unit_id": "slang_engine", "unit_kind": "component"}
    rationale = {
        "run_id": run_id,
        "phase_counts": phase_counts,
        "mean_v14": mean_v14,
        "mean_risk": mean_risk,
        "score": float(0.45 + 0.35 * _clamp(mean_v14) + 0.2 * _clamp(mean_risk)),
    }
    recommended_change = {
        "watch_terms": watch_terms,
        "phase_focus": sorted(list(phase_counts.keys())),
    }
    payload = {
        "kind": ProposalKind.COMPONENT_FOCUS_SUGGESTION.value,
        "target": target,
        "recommended_change": recommended_change,
        "rationale": rationale,
    }
    proposal_id = f"epp_{hash_canonical_json(payload)[:16]}"
    return [
        EvolutionProposal(
            proposal_id=proposal_id,
            kind=ProposalKind.COMPONENT_FOCUS_SUGGESTION,
            target=target,
            rationale=rationale,
            recommended_change=recommended_change,
            expected_impact={"metric": "novelty_capture", "delta": 0.015},
            risk={"integrity_risk": _clamp(mean_risk), "coverage_risk": 0.05},
            confidence=float(0.6 + 0.2 * _clamp(mean_v14)),
            provenance={"a2_phase_path": a2_phase_path},
        )
    ]


def _proposals_from_gate(
    *,
    run_id: str,
    gate: Optional[Dict[str, Any]],
    forecast_score_path: Optional[str],
) -> List[EvolutionProposal]:
    if not isinstance(gate, dict):
        return []
    escalation = str(gate.get("evidence_escalation") or "none")
    if escalation == "none":
        return []

    target = {"unit_id": "forecast_gate", "unit_kind": "gate_policy"}
    recommended_change = {
        "action": escalation,
        "note": "Gate policy requests stronger evidence under current fog conditions.",
    }
    rationale = {
        "evidence_escalation": escalation,
        "eeb_multiplier": gate.get("eeb_multiplier"),
        "score": 0.6 if escalation == "online_escalation" else 0.75,
    }
    payload = {
        "kind": ProposalKind.EVIDENCE_ESCALATION.value,
        "target": target,
        "recommended_change": recommended_change,
        "rationale": rationale,
    }
    proposal_id = f"epp_{hash_canonical_json(payload)[:16]}"
    return [
        EvolutionProposal(
            proposal_id=proposal_id,
            kind=ProposalKind.EVIDENCE_ESCALATION,
            target=target,
            rationale=rationale,
            recommended_change=recommended_change,
            expected_impact={"metric": "evidence_quality", "delta": 0.02},
            risk={"integrity_risk": 0.1, "coverage_risk": 0.08},
            confidence=0.62 if escalation == "online_escalation" else 0.7,
            provenance={"forecast_score_path": forecast_score_path, "run_id": run_id},
        )
    ]


def _proposals_from_audit(
    *,
    run_id: str,
    audit: Optional[Dict[str, Any]],
    audit_path: Optional[str],
) -> List[EvolutionProposal]:
    out: List[EvolutionProposal] = []
    if not isinstance(audit, dict):
        return out
    calibration = audit.get("calibration") or {}
    if not isinstance(calibration, dict) or not calibration:
        return out

    worst: Optional[tuple[float, int, str]] = None
    best: Optional[tuple[float, int, str]] = None
    for horizon, payload in calibration.items():
        if not isinstance(payload, dict):
            continue
        brier = payload.get("brier")
        n = payload.get("n")
        if brier is None or n is None:
            continue
        brier = float(brier)
        n = int(n)
        if worst is None or brier > worst[0]:
            worst = (brier, n, str(horizon))
        if best is None or brier < best[0]:
            best = (brier, n, str(horizon))

    def proposal_id(kind: ProposalKind, suffix: str, payload: Dict[str, Any]) -> str:
        base = {"kind": kind.value, "suffix": suffix, "payload": payload}
        return f"epp_{hash_canonical_json(base)[:16]}"

    if worst:
        brier, n, horizon = worst
        if brier > 0.28 and n >= 8:
            target = {"policy": "forecast_horizon_gate", "horizon": horizon}
            recommended_change = {
                "action": "tighten",
                "note": (
                    f"Brier {brier:.3f} on {horizon} (n={n}) "
                    "indicates poor calibration; restrict or require stronger eligibility."
                ),
                "suggested_gate": {
                    "disable_horizon": horizon,
                    "fallback_allowed": ["days", "weeks", "months"]
                    if horizon.startswith("years")
                    else ["days", "weeks"],
                },
            }
            payload = {
                "kind": ProposalKind.CALIBRATION_POLICY_ADJUSTMENT.value,
                "target": target,
                "recommended_change": recommended_change,
            }
            out.append(
                EvolutionProposal(
                    proposal_id=proposal_id(
                        ProposalKind.CALIBRATION_POLICY_ADJUSTMENT, f"tighten_{horizon}", payload
                    ),
                    kind=ProposalKind.CALIBRATION_POLICY_ADJUSTMENT,
                    target=target,
                    rationale={"brier": brier, "n": n, "score": float(1.0 - brier)},
                    recommended_change=recommended_change,
                    expected_impact={"metric": "integrity", "delta": 0.015},
                    risk={"coverage_risk": 0.10},
                    confidence=0.7,
                    provenance={"audit_path": audit_path},
                )
            )

            target = {"scope": "long_horizon_predictions", "horizon": horizon}
            recommended_change = {
                "user_prompt": (
                    "Long-horizon predictions now require offline evidence packs "
                    "and primary-source links."
                )
            }
            payload = {
                "kind": ProposalKind.OFFLINE_EVIDENCE_ESCALATION.value,
                "target": target,
                "recommended_change": recommended_change,
            }
            out.append(
                EvolutionProposal(
                    proposal_id=proposal_id(
                        ProposalKind.OFFLINE_EVIDENCE_ESCALATION, f"evidence_{horizon}", payload
                    ),
                    kind=ProposalKind.OFFLINE_EVIDENCE_ESCALATION,
                    target=target,
                    rationale={"brier": brier, "n": n, "score": float(1.0 - brier)},
                    recommended_change=recommended_change,
                    expected_impact={"metric": "truth_integrity", "delta": 0.01},
                    risk={"cost_risk": 0.10},
                    confidence=0.65,
                    provenance={"audit_path": audit_path},
                )
            )

    if best:
        brier, n, horizon = best
        if brier < 0.18 and n >= 25:
            target = {"policy": "forecast_horizon_gate", "horizon": horizon}
            recommended_change = {
                "action": "loosen",
                "note": (
                    f"Brier {brier:.3f} on {horizon} (n={n}) is strong; cautiously allow "
                    "longer horizons only for low-risk plateau with long half-life."
                ),
                "suggested_gate_delta": {
                    "eligibility_stricter": True,
                    "half_life_days_fit_min": 45.0,
                    "manipulation_risk_max": 0.20,
                },
            }
            payload = {
                "kind": ProposalKind.CALIBRATION_POLICY_ADJUSTMENT.value,
                "target": target,
                "recommended_change": recommended_change,
            }
            out.append(
                EvolutionProposal(
                    proposal_id=proposal_id(
                        ProposalKind.CALIBRATION_POLICY_ADJUSTMENT, f"loosen_{horizon}", payload
                    ),
                    kind=ProposalKind.CALIBRATION_POLICY_ADJUSTMENT,
                    target=target,
                    rationale={"brier": brier, "n": n, "score": float(1.0 - brier)},
                    recommended_change=recommended_change,
                    expected_impact={"metric": "long_horizon_precision", "delta": 0.01},
                    risk={"integrity_risk": 0.05},
                    confidence=0.6,
                    provenance={"audit_path": audit_path},
                )
            )

    return out
