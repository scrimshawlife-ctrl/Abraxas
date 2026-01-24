from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

from abraxas_ase.candidates import CandidateRec, load_candidates_jsonl, write_candidates_jsonl
from abraxas_ase.hysteresis import HysteresisParams, LANE_ORDER, apply_hysteresis, state_from_dict, state_to_dict
from abraxas_ase.lps import LPSParams, compute_lps, lane_decision
from abraxas_ase.provenance import stable_json_dumps
from abraxas_ase.stabilization import StabilizationParams, apply_stabilization


def _uniq_sorted(xs: List[str]) -> List[str]:
    return sorted(set(xs))


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m abraxas_ase.tools.candidate_update")
    ap.add_argument("--report", required=True, help="Path to ASE daily_report.json")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--candidates", required=True, help="Path to candidates.jsonl (snapshot)")
    ap.add_argument("--out-metrics", default="", help="Optional: write scoring decisions json")
    args = ap.parse_args()

    report_path = Path(args.report)
    rep = json.loads(report_path.read_text(encoding="utf-8"))
    if "verified_sub_anagrams" not in rep or "clusters" not in rep:
        raise SystemExit("candidate_update requires academic or enterprise tier report with verified_sub_anagrams and clusters.")

    # Load existing candidates snapshot
    cur = load_candidates_jsonl(args.candidates)

    date = args.date
    params = LPSParams()
    hyst_params = HysteresisParams()
    stab_params = StabilizationParams()

    # Build observation sets from report
    # Tokens: from high_tap_tokens list
    obs_tokens = rep.get("high_tap_tokens", [])
    # Subwords: from verified_sub_anagrams
    obs_subs = rep.get("verified_sub_anagrams", [])
    # PFDI alerts (if any)
    obs_pfdi = rep.get("pfdi_alerts", [])

    clusters = rep.get("clusters", {}).get("by_item_id", {})
    sas_rows = rep.get("sas", {}).get("rows", [])
    sas_by_sub = {r["sub"]: float(r["sas"]) for r in sas_rows}
    has_sas = bool(sas_rows)

    # Map pfdi by subword (max)
    pfdi_by_sub = {}
    for a in obs_pfdi:
        sub = a["sub"]
        pfdi_by_sub[sub] = max(float(pfdi_by_sub.get(sub, 0.0)), float(a.get("pfdi", 0.0)))

    # token occurrences from tier2 hits (real provenance)
    token_sources = {}
    token_events = {}
    for h in obs_subs:
        tok = h["token"]
        token_sources.setdefault(tok, set()).add(h.get("source", "*"))
        item_id = h.get("item_id", "")
        ev = clusters.get(item_id, f"item:{item_id}") if item_id else f"run:{rep.get('run_id','')}"
        token_events.setdefault(tok, set()).add(ev)

    decisions = []
    suggested_counts = {"candidate": 0, "shadow": 0, "canary": 0, "core": 0}
    final_counts = {"candidate": 0, "shadow": 0, "canary": 0, "core": 0}
    promotions = 0
    demotions = 0
    hysteresis_waits = 0
    stabilization_blocks = 0

    # Update TOKEN candidates
    for t in obs_tokens:
        tok = t["token"]
        key = ("token", tok)
        prev = cur.get(key)
        sources = [] if prev is None else list(prev.sources)
        events = [] if prev is None else list(prev.events)

        real_sources = sorted(token_sources.get(tok, set()))
        real_events = sorted(token_events.get(tok, set()))
        sources = _uniq_sorted(sources + real_sources)
        events = _uniq_sorted(events + real_events)

        if prev is None:
            rec = CandidateRec(
                candidate=tok,
                kind="token",
                date_first_seen=date,
                date_last_seen=date,
                days_seen=1,
                sources=sources,
                events=events,
                tap_max=float(t["tap"]),
                sas_sum=0.0,
                pfdi_max=0.0,
                mentions_total=1,
                lane="candidate",
            )
        else:
            rec = CandidateRec(
                candidate=tok,
                kind="token",
                date_first_seen=prev.date_first_seen,
                date_last_seen=date,
                days_seen=prev.days_seen + 1,
                sources=sources,
                events=events,
                tap_max=max(prev.tap_max, float(t["tap"])),
                sas_sum=prev.sas_sum,
                pfdi_max=prev.pfdi_max,
                mentions_total=prev.mentions_total + 1,
                lane=prev.lane,
            )

        lps = compute_lps(
            tap_max=rec.tap_max,
            sas_sum=rec.sas_sum,
            pfdi_max=rec.pfdi_max,
            days_seen=rec.days_seen,
            sources_count=len(rec.sources),
            events_count=len(rec.events),
            mentions_total=rec.mentions_total,
            params=params,
        )
        suggested_lane = lane_decision(
            lps=lps,
            days_seen=rec.days_seen,
            sources_count=len(rec.sources),
            events_count=len(rec.events),
            params=params,
        )
        prev_lane = prev.lane if prev else "candidate"
        prev_hyst = state_from_dict(prev.hysteresis if prev else None)
        lane_after_hyst, new_hyst_state, hyst_info = apply_hysteresis(suggested_lane, prev_hyst, hyst_params)
        lane_final, cycles_alive, cycles_stable, blocked = apply_stabilization(
            lane_final=lane_after_hyst,
            prev_lane=prev_lane,
            prev_cycles_alive=prev.cycles_alive if prev else 0,
            prev_cycles_stable=prev.cycles_stable if prev else 0,
            params=stab_params,
        )

        if hyst_info.get("reason") == "promote_wait" or hyst_info.get("reason") == "demote_wait":
            hysteresis_waits += 1
        if blocked:
            stabilization_blocks += 1

        prev_rank = LANE_ORDER.get(prev_lane, 0)
        final_rank = LANE_ORDER.get(lane_final, 0)
        if final_rank > prev_rank:
            promotions += 1
        elif final_rank < prev_rank:
            demotions += 1

        suggested_counts[suggested_lane] += 1
        final_counts[lane_final] += 1

        rec2 = CandidateRec(**{**rec.__dict__, "lane": lane_final, "hysteresis": state_to_dict(new_hyst_state), "cycles_alive": cycles_alive, "cycles_stable": cycles_stable})
        cur[key] = rec2
        decisions.append({
            "kind": "token",
            "candidate": tok,
            "lps": lps,
            "lane_suggested": suggested_lane,
            "lane_final": lane_final,
            "days_seen": rec2.days_seen,
            "hysteresis_reason": hyst_info.get("reason"),
            "stabilization_blocked": blocked,
        })

    sub_mentions = {}
    sub_sources = {}
    sub_events = {}
    for h in obs_subs:
        sub = h["sub"]
        src = h.get("source", "*")
        item_id = h.get("item_id", "")
        event_key = clusters.get(item_id, f"item:{item_id}") if item_id else f"run:{rep.get('run_id','')}"
        sub_mentions[sub] = sub_mentions.get(sub, 0) + 1
        sub_sources.setdefault(sub, set()).add(src)
        sub_events.setdefault(sub, set()).add(event_key)

    for sub in sorted(sub_mentions):
        key = ("subword", sub)
        prev = cur.get(key)
        sources = [] if prev is None else list(prev.sources)
        events = [] if prev is None else list(prev.events)
        sources = _uniq_sorted(sources + sorted(sub_sources.get(sub, set())))
        events = _uniq_sorted(events + sorted(sub_events.get(sub, set())))

        pfdi_max = max(float(prev.pfdi_max) if prev else 0.0, float(pfdi_by_sub.get(sub, 0.0)))
        mentions_today = sub_mentions.get(sub, 0)
        if has_sas:
            today_sas = float(sas_by_sub.get(sub, 0.0))
        else:
            today_sas = float(mentions_today)

        if prev is None:
            rec = CandidateRec(
                candidate=sub,
                kind="subword",
                date_first_seen=date,
                date_last_seen=date,
                days_seen=1,
                sources=sources,
                events=events,
                tap_max=0.0,
                sas_sum=today_sas,
                pfdi_max=pfdi_max,
                mentions_total=mentions_today,
                lane="candidate",
            )
        else:
            rec = CandidateRec(
                candidate=sub,
                kind="subword",
                date_first_seen=prev.date_first_seen,
                date_last_seen=date,
                days_seen=prev.days_seen + 1,
                sources=sources,
                events=events,
                tap_max=0.0,
                sas_sum=prev.sas_sum + today_sas,
                pfdi_max=pfdi_max,
                mentions_total=prev.mentions_total + mentions_today,
                lane=prev.lane,
            )

        lps = compute_lps(
            tap_max=rec.tap_max,
            sas_sum=rec.sas_sum,
            pfdi_max=rec.pfdi_max,
            days_seen=rec.days_seen,
            sources_count=len(rec.sources),
            events_count=len(rec.events),
            mentions_total=rec.mentions_total,
            params=params,
        )
        suggested_lane = lane_decision(
            lps=lps,
            days_seen=rec.days_seen,
            sources_count=len(rec.sources),
            events_count=len(rec.events),
            params=params,
        )
        prev_lane = prev.lane if prev else "candidate"
        prev_hyst = state_from_dict(prev.hysteresis if prev else None)
        lane_after_hyst, new_hyst_state, hyst_info = apply_hysteresis(suggested_lane, prev_hyst, hyst_params)
        lane_final, cycles_alive, cycles_stable, blocked = apply_stabilization(
            lane_final=lane_after_hyst,
            prev_lane=prev_lane,
            prev_cycles_alive=prev.cycles_alive if prev else 0,
            prev_cycles_stable=prev.cycles_stable if prev else 0,
            params=stab_params,
        )

        if hyst_info.get("reason") == "promote_wait" or hyst_info.get("reason") == "demote_wait":
            hysteresis_waits += 1
        if blocked:
            stabilization_blocks += 1

        prev_rank = LANE_ORDER.get(prev_lane, 0)
        final_rank = LANE_ORDER.get(lane_final, 0)
        if final_rank > prev_rank:
            promotions += 1
        elif final_rank < prev_rank:
            demotions += 1

        suggested_counts[suggested_lane] += 1
        final_counts[lane_final] += 1

        rec2 = CandidateRec(**{**rec.__dict__, "lane": lane_final, "hysteresis": state_to_dict(new_hyst_state), "cycles_alive": cycles_alive, "cycles_stable": cycles_stable})
        cur[key] = rec2
        decisions.append({
            "kind": "subword",
            "candidate": sub,
            "lps": lps,
            "lane_suggested": suggested_lane,
            "lane_final": lane_final,
            "days_seen": rec2.days_seen,
            "hysteresis_reason": hyst_info.get("reason"),
            "stabilization_blocked": blocked,
        })

    # Write snapshot deterministically
    write_candidates_jsonl(args.candidates, list(cur.values()))

    if args.out_metrics:
        total = max(1, len(cur))
        promotion_ratio = promotions / total
        demotion_ratio = demotions / total
        drift = {
            "promotion_ratio": promotion_ratio,
            "demotion_ratio": demotion_ratio,
            "promotion_gate": promotion_ratio > 0.2,
            "demotion_gate": demotion_ratio > 0.2,
        }
        Path(args.out_metrics).write_text(
            stable_json_dumps({
                "date": date,
                "decisions": sorted(decisions, key=lambda d: (d["kind"], d["candidate"])),
                "summary": {
                    "suggested_counts": suggested_counts,
                    "final_counts": final_counts,
                    "promotions": promotions,
                    "demotions": demotions,
                    "hysteresis_waits": hysteresis_waits,
                    "stabilization_blocks": stabilization_blocks,
                    "drift_gates": drift,
                },
            }) + "\n",
            encoding="utf-8",
        )

    print(stable_json_dumps({"status":"ok","candidates":len(cur)}))


if __name__ == "__main__":
    main()
