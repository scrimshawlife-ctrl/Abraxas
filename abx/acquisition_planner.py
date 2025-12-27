from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _latest(dir_path: str, pattern: str) -> str:
    paths = sorted(glob.glob(os.path.join(dir_path, pattern)))
    return paths[-1] if paths else ""


def _clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return float(max(a, min(b, x)))


def _cost(mode: str) -> float:
    # rough deterministic cost weights (entropy/time), tunable.
    m = (mode or "").lower().strip()
    if m == "offline":
        return 0.65
    if m == "decodo":
        return 0.45
    if m == "online":
        return 0.35
    if m == "manual":
        return 0.25
    return 0.40


def _uplift_hint(task_kind: str) -> Dict[str, float]:
    """
    Expected improvements (heuristic). These are *claims about uplift*, not guarantees.
    """
    tk = (task_kind or "").upper().strip()
    if tk == "ADD_PRIMARY_ANCHORS":
        return {"PIS": +0.10, "CSHL_days": -3.0, "TTT_0.8_days": -2.0}
    if tk == "INCREASE_DOMAIN_DIVERSITY":
        return {"PIS": +0.08, "CSHL_days": -2.0, "TTT_0.8_days": -1.5}
    if tk == "ADD_FALSIFICATION_TESTS":
        return {"CSHL_days": -4.0, "TTT_0.8_days": -3.0}
    if tk == "FETCH_COUNTERCLAIMS_DISJOINT":
        return {"CSHL_days": -1.0, "TTT_0.8_days": -1.0, "ML_score": -0.06}
    if tk == "VERIFY_MEDIA_ORIGIN":
        return {"ML_score": -0.10, "PIS": +0.06}
    if tk == "ENTITY_GROUNDING":
        return {"CSHL_days": -1.5, "TTT_0.8_days": -1.0}
    return {}


def _load_uplift_table(path: str = "out/config/uplift_table.json") -> Dict[str, Dict[str, float]]:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            t = obj.get("table") if isinstance(obj, dict) else None
            return t if isinstance(t, dict) else {}
    except Exception:
        return {}
    return {}


def _task(
    *,
    claim_id: str,
    term: str,
    title: str,
    task_kind: str,
    mode: str,
    steps: List[str],
    why: str,
    priority: float,
    expected_uplift: Dict[str, float],
    depends_on: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "task_id": f"{claim_id[:10]}_{task_kind.lower()}",
        "claim_id": claim_id,
        "term": term,
        "title": title,
        "task_kind": task_kind,
        "mode": mode,
        "why": why,
        "steps": steps,
        "depends_on": depends_on or [],
        "expected_uplift": expected_uplift,
        "cost": _cost(mode),
        "priority": float(_clamp(priority, 0.0, 1.0)),
        "notes": "Task is an acquisition action. Not executed here. Designed for Decodo/online/offline/manual pipelines.",
    }


def plan_from_deficits(
    *,
    time_to_truth: Dict[str, Any],
    sig_kpi: Dict[str, Any],
    proof_integrity: Dict[str, Any],
    regime_shift: Dict[str, Any],
    max_tasks_per_claim: int = 6,
) -> Dict[str, Any]:
    calibrated = _load_uplift_table()
    claims = time_to_truth.get("claims") if isinstance(time_to_truth.get("claims"), dict) else {}
    pdg = sig_kpi.get("PDG") if isinstance(sig_kpi.get("PDG"), dict) else {}
    pis = float(proof_integrity.get("PIS") or 0.0) if isinstance(proof_integrity, dict) else 0.0
    regime = bool(regime_shift.get("regime_shift")) if isinstance(regime_shift, dict) else False

    avg_domains = float(pdg.get("avg_unique_domains_per_term") or 0.0)
    avg_primary = float(pdg.get("avg_primary_anchor_ratio") or 0.0)
    avg_tests = float(pdg.get("avg_falsification_tests_per_term") or 0.0)

    tasks: List[Dict[str, Any]] = []

    for cid, v in claims.items():
        if not isinstance(v, dict):
            continue
        term = str(v.get("term") or "")
        cshl = float(v.get("CSHL_days") or -1.0)
        ttt08 = float(v.get("TTT_0.8_days") or -1.0)
        fr = float(v.get("flip_rate") or 0.0)
        latest = v.get("latest") if isinstance(v.get("latest"), dict) else {}
        ml = float(latest.get("ML_score") or 0.0)
        cs = float(latest.get("CS_score") or 0.0)

        # deficit signals
        unstable = (cshl < 0) or (cshl > 21) or (fr > 0.35) or (ttt08 < 0)
        polluted = (ml >= 0.65) or (regime and ml >= 0.55)
        weak_testing = avg_tests < 1.2
        weak_domains = avg_domains < 3.0
        weak_primary = avg_primary < 0.25
        low_pis = pis < 0.55

        per_claim: List[Dict[str, Any]] = []

        if unstable and weak_testing:
            per_claim.append(_task(
                claim_id=cid,
                term=term,
                title="Add falsification tests to stabilize claim",
                task_kind="ADD_FALSIFICATION_TESTS",
                mode="manual",
                why="High instability / slow stabilization is often reduced by explicit tests that can fail.",
                steps=[
                    "Define 3 falsification tests (what would disprove this claim?).",
                    "Define 2 competing hypotheses (adjacent explanations).",
                    "Harvest at least 2 anchors per hypothesis (primary if possible).",
                    "Log tests + outcomes in term ledger and evidence graph edges (SUPPORTS/CONTRADICTS).",
                ],
                priority=0.82,
                expected_uplift=(calibrated.get("ADD_FALSIFICATION_TESTS") or _uplift_hint("ADD_FALSIFICATION_TESTS")),
            ))

        if unstable and weak_domains:
            per_claim.append(_task(
                claim_id=cid,
                term=term,
                title="Increase domain diversity for this claim",
                task_kind="INCREASE_DOMAIN_DIVERSITY",
                mode="decodo",
                why="Low domain diversity inflates volatility and makes coherence look higher/lower than it is.",
                steps=[
                    "Use Decodo to fetch 6–10 sources across disjoint domains (include non-mainstream + mainstream + primary).",
                    "Ensure at least 4 unique domains are added for this claim window.",
                    "Append anchors to anchor_ledger (mark primary where applicable).",
                    "Link anchors to claim with SUPPORTS/CONTRADICTS edges.",
                ],
                priority=0.76,
                expected_uplift=(calibrated.get("INCREASE_DOMAIN_DIVERSITY") or _uplift_hint("INCREASE_DOMAIN_DIVERSITY")),
            ))

        if (unstable and weak_primary) or low_pis:
            per_claim.append(_task(
                claim_id=cid,
                term=term,
                title="Add primary anchors to improve proof integrity",
                task_kind="ADD_PRIMARY_ANCHORS",
                mode="online",
                why="Primary sourcing reduces duplicate laundering and raises PIS, tightening uncertainty bands.",
                steps=[
                    "Locate 2–3 primary sources (papers, court docs, filings, direct transcripts, raw datasets).",
                    "Append anchors with --primary to anchor_ledger.",
                    "Link each anchor to claim with relation SUPPORTS or CONTRADICTS.",
                ],
                priority=0.71,
                expected_uplift=(calibrated.get("ADD_PRIMARY_ANCHORS") or _uplift_hint("ADD_PRIMARY_ANCHORS")),
            ))

        if polluted:
            per_claim.append(_task(
                claim_id=cid,
                term=term,
                title="Fetch counterclaims from disjoint communities",
                task_kind="FETCH_COUNTERCLAIMS_DISJOINT",
                mode="decodo",
                why="High ML_score indicates possible manipulation; disjoint counterclaims reduce echo-chamber bias.",
                steps=[
                    "Query disjoint communities (different political/cultural clusters) for alternative narratives.",
                    "Collect at least 3 counterclaim anchors from ≥2 distinct domains.",
                    "Link with CONTRADICTS edges where appropriate.",
                    "Recompute truth_contamination map.",
                ],
                priority=0.80,
                expected_uplift=(calibrated.get("FETCH_COUNTERCLAIMS_DISJOINT") or _uplift_hint("FETCH_COUNTERCLAIMS_DISJOINT")),
            ))

        if polluted:
            per_claim.append(_task(
                claim_id=cid,
                term=term,
                title="Verify media origin / manipulation risk (if media anchors present)",
                task_kind="VERIFY_MEDIA_ORIGIN",
                mode="offline",
                why="Deepfakes and synthetic content pollute anchors; origin checks reduce ML_score.",
                steps=[
                    "For image/video anchors: record first-seen timestamp, platform, uploader, and any available metadata.",
                    "Check for cross-platform mismatch (same clip with different captions/time).",
                    "Log findings as anchors (offline notes) and link to claim as SUPPORTS/CONTRADICTS/REFRAMES.",
                ],
                priority=0.74,
                expected_uplift=(calibrated.get("VERIFY_MEDIA_ORIGIN") or _uplift_hint("VERIFY_MEDIA_ORIGIN")),
            ))

        if unstable and (term or ""):
            per_claim.append(_task(
                claim_id=cid,
                term=term,
                title="Entity-ground this claim for causal clarity",
                task_kind="ENTITY_GROUNDING",
                mode="manual",
                why="Vague entities inflate instability; grounding reduces causal ambiguity and improves stabilization.",
                steps=[
                    "Identify 2–5 entities (people/orgs/places/products) actually involved.",
                    "Link entities in evidence graph (entity_linked) with relation ABOUT/TARGETS/BENEFITS/HARMS.",
                    "Add one anchor per entity relationship (if possible).",
                ],
                priority=0.62,
                expected_uplift=(calibrated.get("ENTITY_GROUNDING") or _uplift_hint("ENTITY_GROUNDING")),
            ))

        # rank within claim by (priority - cost penalty)
        per_claim = sorted(per_claim, key=lambda t: float(t.get("priority", 0.0)) - 0.25 * float(t.get("cost", 0.0)), reverse=True)
        tasks.extend(per_claim[:max_tasks_per_claim])

    # global ranking
    tasks = sorted(tasks, key=lambda t: float(t.get("priority", 0.0)) - 0.25 * float(t.get("cost", 0.0)), reverse=True)

    return {
        "version": "acquisition_plan.v0.1",
        "ts": _utc_now_iso(),
        "globals": {
            "PIS": float(pis),
            "avg_unique_domains_per_term": float(avg_domains),
            "avg_primary_anchor_ratio": float(avg_primary),
            "avg_falsification_tests_per_term": float(avg_tests),
            "regime_shift": bool(regime),
        },
        "n_tasks": len(tasks),
        "tasks": tasks,
        "notes": "Acquisition plan generated from temporal stabilization deficits (CSHL/TTT/flip_rate) and integrity context (PIS/PDG).",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate acquisition tasks from stabilization deficits")
    ap.add_argument("--time-to-truth", default="")
    ap.add_argument("--sig-kpi", default="")
    ap.add_argument("--proof-integrity", default="")
    ap.add_argument("--regime-shift", default="")
    ap.add_argument("--max-tasks-per-claim", type=int, default=6)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    ttt_path = args.time_to_truth or _latest("out/reports", "time_to_truth_*.json")
    sig_path = args.sig_kpi or _latest("out/reports", "sig_kpi_*.json")
    pis_path = args.proof_integrity or _latest("out/reports", "proof_integrity_*.json")
    reg_path = args.regime_shift or _latest("out/reports", "regime_shift_*.json")

    if not ttt_path:
        raise SystemExit("No time_to_truth report found. Run `python -m abx.claim_timeseries` and `python -m abx.time_to_truth` first.")

    obj = plan_from_deficits(
        time_to_truth=_read_json(ttt_path),
        sig_kpi=_read_json(sig_path) if sig_path else {},
        proof_integrity=_read_json(pis_path) if pis_path else {},
        regime_shift=_read_json(reg_path) if reg_path else {},
        max_tasks_per_claim=int(args.max_tasks_per_claim),
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/reports", f"acquisition_plan_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[ACQ_PLAN] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
