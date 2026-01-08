from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from abraxas.memetic.metrics_reduce import reduce_provenance_means
from abraxas.memetic.term_consensus_map import load_term_consensus_map
from abraxas.memetic.temporal import build_temporal_profiles
# classify_term replaced by forecast.term.classify capability
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext
from abx.truth_pollution import compute_tpi_for_run


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main() -> int:
    p = argparse.ArgumentParser(description="A2 Phase/Temporal Profiles v0.1")
    p.add_argument("--run-id", required=True)
    p.add_argument("--registry", default="out/a2_registry/terms.jsonl")
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--mwr", default=None, help="MWR artifact path to copy DMX snapshot")
    p.add_argument("--max-terms", type=int, default=500)
    p.add_argument("--min-obs", type=int, default=2)
    p.add_argument("--now", default=None, help="Optional ISO now override")
    p.add_argument("--value-ledger", default="out/value_ledgers/a2_phase_runs.jsonl")
    args = p.parse_args()

    # Create rune invocation context for capability calls
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.a2_phase",
        git_hash="unknown"
    )

    ts = _utc_now_iso()
    profiles_full = build_temporal_profiles(
        args.registry,
        now_iso=args.now,
        max_terms=2000000,
        min_obs=int(args.min_obs),
    )
    profiles_view = profiles_full[: int(args.max_terms)]

    profiles_full_dicts = [p.to_dict() for p in profiles_full]
    means = reduce_provenance_means(profiles_full_dicts)

    dmx = {}
    try:
        mwr_path = args.mwr or os.path.join(args.out_reports, f"mwr_{args.run_id}.json")
        if os.path.exists(mwr_path):
            with open(mwr_path, "r", encoding="utf-8") as f:
                mwr = json.load(f)
            if isinstance(mwr, dict) and isinstance(mwr.get("dmx"), dict):
                dmx = mwr.get("dmx") or {}
    except Exception:
        dmx = {}

    try:
        claims_path = os.path.join(args.out_reports, f"claims_{args.run_id}.json")
        if os.path.exists(claims_path):
            with open(claims_path, "r", encoding="utf-8") as f:
                claims = json.load(f)
            if isinstance(claims, dict) and isinstance(claims.get("metrics"), dict):
                consensus_gap = float(claims.get("metrics", {}).get("consensus_gap") or 0.0)
                means["consensus_gap_mean"] = consensus_gap
    except Exception:
        pass
    # term consensus handled via load_term_consensus_map below

    term_claims_path = os.path.join(args.out_reports, f"term_claims_{args.run_id}.json")
    term_gap = load_term_consensus_map(term_claims_path)

    def _annotate_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
        out_profile = dict(profile)
        term = str(out_profile.get("term") or "").strip().lower()
        if term and term in term_gap:
            out_profile["consensus_gap_term"] = float(term_gap[term])
        else:
            out_profile["consensus_gap_term"] = 0.0
            flags = out_profile.get("flags")
            if not isinstance(flags, list):
                flags = []
            flags.append("CONSENSUS_MISSING")
            out_profile["flags"] = flags
        return out_profile

    profiles_full_dicts = [_annotate_profile(p.to_dict()) for p in profiles_full]
    profiles_view_dicts = [_annotate_profile(p.to_dict()) for p in profiles_view]
    if profiles_full_dicts:
        means["term_consensus_gap_mean"] = float(
            sum(p.get("consensus_gap_term") or 0.0 for p in profiles_full_dicts)
            / float(len(profiles_full_dicts))
        )

    evidence_index_path = os.path.join(args.out_reports, f"evidence_index_{args.run_id}.json")
    bundles_result = invoke_capability(
        "evidence.lift.load_bundles_from_index",
        {
            "bundles_dir": "out/evidence_bundles",
            "index_path": evidence_index_path
        },
        ctx=ctx,
        strict_execution=True
    )
    bundles = bundles_result["bundles"]

    lift_result = invoke_capability(
        "evidence.lift.term_lift",
        {"bundles": bundles},
        ctx=ctx,
        strict_execution=True
    )
    lift_by_term = lift_result["lift_by_term"]
    bundles_by_term: Dict[str, List[Dict[str, Any]]] = {}
    for bundle in bundles:
        terms = bundle.get("terms") if isinstance(bundle.get("terms"), list) else []
        for term in terms:
            key = str(term or "").strip().lower()
            if key:
                bundles_by_term.setdefault(key, []).append(bundle)

    def _apply_evidence_lift(profile: Dict[str, Any]) -> Dict[str, Any]:
        out_profile = dict(profile)
        term = str(out_profile.get("term") or "").strip().lower()
        if not term:
            return out_profile
        lift = lift_by_term.get(term)
        if not lift:
            return out_profile

        att0 = float(out_profile.get("attribution_strength") or 0.0)
        sd0 = float(out_profile.get("source_diversity") or 0.0)
        uplift_result = invoke_capability(
            "evidence.lift.uplift_factors",
            {"lift": lift},
            ctx=ctx,
            strict_execution=True
        )
        att_u = uplift_result["attribution_uplift"]
        sd_u = uplift_result["diversity_uplift"]

        att1 = min(1.0, max(0.0, att0 + att_u))
        sd1 = min(1.0, max(0.0, sd0 + sd_u))

        out_profile["evidence_lift"] = {
            "bundle_count": int(lift.get("bundle_count") or 0),
            "source_types": lift.get("source_types") or {},
            "credence_mean": float(lift.get("credence_mean") or 0.0),
            "attribution_uplift": float(att_u),
            "diversity_uplift": float(sd_u),
        }
        out_profile["attribution_strength_uplifted"] = float(att1)
        out_profile["source_diversity_uplifted"] = float(sd1)
        flags = out_profile.get("flags")
        if not isinstance(flags, list):
            flags = []
        flags.append("EVIDENCE_UPLIFT_APPLIED")
        out_profile["flags"] = flags

        ev = bundles_by_term.get(term, [])
        if ev:
            pi_scores = []
            sml_scores = []
            sml_high = 0
            for bundle in ev:
                dl = (
                    bundle.get("disinfo_labels")
                    if isinstance(bundle.get("disinfo_labels"), dict)
                    else {}
                )
                pi = dl.get("PI") if isinstance(dl.get("PI"), dict) else {}
                sml = dl.get("SML") if isinstance(dl.get("SML"), dict) else {}
                ps = float(pi.get("score") or 0.0)
                ss = float(sml.get("score") or 0.0)
                pi_scores.append(ps)
                sml_scores.append(ss)
                if str(sml.get("bucket") or "") == "HIGH":
                    sml_high += 1
            out_profile["disinfo_evidence_summary"] = {
                "bundle_count": len(ev),
                "pi_risk_mean": sum(pi_scores) / len(pi_scores) if pi_scores else 0.0,
                "sml_mean": sum(sml_scores) / len(sml_scores) if sml_scores else 0.0,
                "sml_high_count": sml_high,
            }
            flags = out_profile.get("flags") if isinstance(out_profile.get("flags"), list) else []
            flags.append("DISINFO_EVIDENCE_SUMMARY")
            out_profile["flags"] = flags
        return out_profile

    profiles_full_dicts = [_apply_evidence_lift(p) for p in profiles_full_dicts]
    profiles_view_dicts = [_apply_evidence_lift(p) for p in profiles_view_dicts]

    evidence_uplift_path = os.path.join(
        args.out_reports, f"evidence_uplift_{args.run_id}.json"
    )
    evidence_uplift: Dict[str, Any] = {}
    if os.path.exists(evidence_uplift_path):
        try:
            with open(evidence_uplift_path, "r", encoding="utf-8") as f:
                evidence_uplift = json.load(f)
        except Exception:
            evidence_uplift = {}
    uplift_terms = (
        evidence_uplift.get("terms")
        if isinstance(evidence_uplift, dict) and isinstance(evidence_uplift.get("terms"), dict)
        else {}
    )

    def _clamp01(x: float) -> float:
        if x < 0.0:
            return 0.0
        if x > 1.0:
            return 1.0
        return float(x)

    def _apply_ledger_uplift(profile: Dict[str, Any]) -> Dict[str, Any]:
        out_profile = dict(profile)
        term = str(out_profile.get("term") or "").strip()
        if not term:
            return out_profile
        uplift = uplift_terms.get(term)
        if not isinstance(uplift, dict):
            return out_profile

        base_att = float(
            out_profile.get("attribution_strength_uplifted")
            or out_profile.get("attribution_strength")
            or 0.0
        )
        base_div = float(
            out_profile.get("source_diversity_uplifted")
            or out_profile.get("source_diversity")
            or 0.0
        )
        up_att = float(uplift.get("uplift_attribution") or 0.0)
        up_div = float(uplift.get("uplift_diversity") or 0.0)

        out_profile["attribution_strength_uplifted"] = _clamp01(base_att + up_att)
        out_profile["source_diversity_uplifted"] = _clamp01(base_div + up_div)
        out_profile["evidence_provenance_index"] = float(
            uplift.get("provenance_index") or 0.0
        )
        out_profile["evidence_uplift"] = {
            "uplift_attribution": float(up_att),
            "uplift_diversity": float(up_div),
            "ff_support": float(uplift.get("ff_support") or 0.0),
            "counts": uplift.get("counts") or {},
        }
        flags = out_profile.get("flags")
        if not isinstance(flags, list):
            flags = []
        flags.append("EVIDENCE_LEDGER_UPLIFT")
        out_profile["flags"] = flags
        return out_profile

    profiles_full_dicts = [_apply_ledger_uplift(p) for p in profiles_full_dicts]
    profiles_view_dicts = [_apply_ledger_uplift(p) for p in profiles_view_dicts]

    tpi_by: Dict[str, Any] = {}
    try:
        ledger_path = "out/ledger/evidence_ledger.jsonl"
        mwr_en_path = os.path.join(
            args.out_reports, f"mwr_enriched_{args.run_id}.json"
        )
        tpi_obj = compute_tpi_for_run(
            run_id=args.run_id,
            out_reports=args.out_reports,
            ledger_path=ledger_path,
            mwr_enriched_path=mwr_en_path,
        )
        tpi_by = (
            tpi_obj.get("per_term")
            if isinstance(tpi_obj, dict) and isinstance(tpi_obj.get("per_term"), dict)
            else {}
        )
    except Exception:
        tpi_by = {}

    def _apply_tpi(profile: Dict[str, Any]) -> Dict[str, Any]:
        out_profile = dict(profile)
        term = str(out_profile.get("term") or "").strip()
        if not term:
            return out_profile
        term_key = " ".join(term.lower().replace("-", " ").replace("_", " ").split())
        tpi = tpi_by.get(term_key)
        if isinstance(tpi, dict):
            out_profile["tpi"] = float(tpi.get("tpi") or 0.0)
            flags = out_profile.get("flags")
            if not isinstance(flags, list):
                flags = []
            flags.append("TPI_ATTACHED")
            out_profile["flags"] = flags
        return out_profile

    profiles_full_dicts = [_apply_tpi(p) for p in profiles_full_dicts]
    profiles_view_dicts = [_apply_tpi(p) for p in profiles_view_dicts]

    # Create context for capability invocations
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.a2_phase",
        git_hash="unknown"
    )

    def _apply_term_csp(profile: Dict[str, Any]) -> Dict[str, Any]:
        out_profile = dict(profile)
        term = str(out_profile.get("term") or "").strip()
        if not term:
            return out_profile
        term_class = invoke_capability(
            "forecast.term.classify",
            {"profile": out_profile},
            ctx=ctx,
            strict_execution=True
        )["term_class"]
        csp_result = invoke_capability(
            "conspiracy.csp.compute_term",
            {
                "term": term,
                "profile": out_profile,
                "dmx_bucket": str(dmx.get("bucket") or "UNKNOWN").upper(),
                "dmx_overall": float(dmx.get("overall_manipulation_risk") or 0.0),
                "term_class": term_class
            },
            ctx=ctx,
            strict_execution=True
        )
        out_profile["term_csp_summary"] = csp_result["term_csp"]
        flags = out_profile.get("flags")
        if not isinstance(flags, list):
            flags = []
        flags.append("CSP_TERM_APPLIED")
        out_profile["flags"] = flags
        return out_profile

    profiles_full_dicts = [_apply_term_csp(p) for p in profiles_full_dicts]
    profiles_view_dicts = [_apply_term_csp(p) for p in profiles_view_dicts]

    out = {
        "version": "a2_phase.v0.2",
        "run_id": args.run_id,
        "ts": ts,
        "registry": args.registry,
        "views": {
            "profiles_top": profiles_view_dicts,
            "profiles_top_n": int(args.max_terms),
        },
        "metrics": means,
        "dmx": dmx,
        "provenance": {"builder": "abx.a2_phase.v0.2"},
    }
    buckets = {
        "surging": [],
        "resurgent": [],
        "emergent": [],
        "plateau": [],
        "decaying": [],
        "dormant": [],
    }
    for p0 in profiles_view_dicts:
        buckets.setdefault(str(p0.get("phase") or "unknown"), []).append(p0)
    top_by_phase = {
        phase: [p0 for p0 in buckets.get(phase, [])[:35]]
        for phase in [
            "surging",
            "resurgent",
            "emergent",
            "plateau",
            "decaying",
            "dormant",
        ]
    }
    out["views"]["top_by_phase"] = top_by_phase

    # Enforce non-truncation policy via capability contract
    ctx_nt = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.a2_phase",
        git_hash="unknown"
    )
    result_nt = invoke_capability(
        capability="evolve.policy.enforce_non_truncation",
        inputs={
            "artifact": out,
            "raw_full": {"profiles": profiles_full_dicts}
        },
        ctx=ctx_nt,
        strict_execution=True
    )
    out = result_nt["artifact"]

    jpath = os.path.join(args.out_reports, f"a2_phase_{args.run_id}.json")
    mpath = os.path.join(args.out_reports, f"a2_phase_{args.run_id}.md")
    _write_json(jpath, out)

    with open(mpath, "w", encoding="utf-8") as f:
        f.write("# A2 Temporal Profiles v0.1\n\n")
        f.write(
            f"- run_id: `{args.run_id}`\n- ts: `{ts}`\n- registry: `{args.registry}`\n\n"
        )
        for phase in [
            "surging",
            "resurgent",
            "emergent",
            "plateau",
            "decaying",
            "dormant",
        ]:
            items = buckets.get(phase, [])
            f.write(f"## {phase} ({len(items)})\n")
            for p0 in items[:35]:
                f.write(
                    f"- **{p0.get('term')}** v14={float(p0.get('v14') or 0.0):.2f} "
                    f"v60={float(p0.get('v60') or 0.0):.2f} "
                    f"hl_fit_days={float(p0.get('half_life_days_fit') or 0.0):.1f} "
                    f"rec_days={p0.get('recurrence_days')} "
                    f"risk={float(p0.get('manipulation_risk_mean') or 0.0):.2f} "
                    f"consensus_gap_term={float(p0.get('consensus_gap_term') or 0.0):.2f} "
                    f"obs={p0.get('obs_n')}\n"
                )
            f.write("\n")

    # Append to value ledger via capability contract
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.a2_phase",
        git_hash="unknown"
    )
    invoke_capability(
        capability="evolve.ledger.append",
        inputs={
            "ledger_path": args.value_ledger,
            "record": {"run_id": args.run_id, "a2_phase_json": jpath, "registry": args.registry}
        },
        ctx=ctx,
        strict_execution=True
    )
    print(f"[A2_PHASE] wrote: {jpath}")
    print(f"[A2_PHASE] wrote: {mpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
