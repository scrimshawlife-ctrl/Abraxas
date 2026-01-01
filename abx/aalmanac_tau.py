from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from abx.task_ledger import task_event


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if isinstance(d, dict):
                    out.append(d)
            except Exception:
                continue
    return out


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _contains_term(term: str, text: str) -> bool:
    t = (term or "").strip()
    if not t or not text:
        return False
    return t.lower() in (text or "").lower()


def _latest_seen(
    term: str, runs: List[Dict[str, Any]], anchors: List[Dict[str, Any]]
) -> Optional[str]:
    latest: Optional[datetime] = None
    latest_iso: Optional[str] = None

    for r in runs:
        if r.get("kind") != "oracle_run":
            continue
        txt = str(r.get("text") or "")
        if not _contains_term(term, txt):
            continue
        ts = _parse_iso(str(r.get("ts") or ""))
        if ts and (latest is None or ts > latest):
            latest = ts
            latest_iso = ts.isoformat()

    for a in anchors:
        title = str(a.get("title") or "")
        hint = str(a.get("content_hint") or "")
        blob = f"{title}\n{hint}"
        if not _contains_term(term, blob):
            continue
        ts = _parse_iso(str(a.get("ts") or ""))
        if ts and (latest is None or ts > latest):
            latest = ts
            latest_iso = ts.isoformat()

    return latest_iso


def _decay_state(age_days: float, half_life_days: float, migration_score: float) -> str:
    if half_life_days <= 0:
        half_life_days = 14.0
    ratio = age_days / half_life_days
    if migration_score >= 0.65 and ratio <= 0.33:
        return "RISING"
    if ratio <= 0.75:
        return "STABLE"
    if ratio <= 1.75:
        return "FADING"
    return "EXTINCT"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="WO-92: enforce τ for AAlmanac terms (decay + next review + tasks)"
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--aalmanac", default="out/ledger/aalmanac.jsonl")
    ap.add_argument("--oracle-ledger", default="out/ledger/oracle_runs.jsonl")
    ap.add_argument("--anchor-ledger", default="out/ledger/anchor_ledger.jsonl")
    ap.add_argument(
        "--migration",
        default="",
        help="Path to latest slang_migration_*.json (default: latest)",
    )
    ap.add_argument("--events-ledger", default="out/ledger/aalmanac_events.jsonl")
    ap.add_argument("--task-ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--out", default="")
    ap.add_argument("--max-terms", type=int, default=60)
    args = ap.parse_args()

    if not args.migration:
        mp = sorted(glob.glob("out/reports/slang_migration_*.json"))
        args.migration = mp[-1] if mp else ""
    mig = _read_json(args.migration) if args.migration else {}
    mig_top = mig.get("top") if isinstance(mig.get("top"), list) else []
    mig_map = {
        str(x.get("term") or ""): float(x.get("migration_score") or 0.0)
        for x in mig_top
        if isinstance(x, dict) and x.get("term")
    }

    canon = [
        e
        for e in _read_jsonl(args.aalmanac)
        if e.get("kind") == "aalmanac_entry"
        and e.get("tier") == "CANON"
        and e.get("term")
    ]
    canon = canon[-int(args.max_terms) :]
    runs = _read_jsonl(args.oracle_ledger)
    anchors = _read_jsonl(args.anchor_ledger)

    now = _utc_now()
    items = []

    for e in canon:
        term = str(e.get("term") or "").strip()
        tau = e.get("tau") if isinstance(e.get("tau"), dict) else {}
        half_life = float(tau.get("half_life_days") or 14.0)
        review_every = float(tau.get("review_every_days") or 7.0)

        seen_iso = _latest_seen(term, runs, anchors)
        seen_dt = _parse_iso(seen_iso) if seen_iso else None
        age_days = (
            float((now - seen_dt).total_seconds() / 86400.0)
            if seen_dt
            else 9999.0
        )

        mig_score = float(mig_map.get(term) or 0.0)
        state = _decay_state(age_days, half_life, mig_score)

        adj = 1.0
        if state == "RISING":
            adj = 0.5
        elif state == "FADING":
            adj = 0.75
        elif state == "EXTINCT":
            adj = 2.0

        next_review_days = max(1.0, min(30.0, review_every * adj))
        next_review_ts = (now + timedelta(days=next_review_days)).isoformat()

        ev = {
            "kind": "aalmanac_tau",
            "ts": _utc_now_iso(),
            "run_id": args.run_id,
            "term": term,
            "last_seen_ts": seen_iso or "",
            "age_days": float(age_days),
            "tau": {
                "half_life_days": float(half_life),
                "review_every_days": float(review_every),
            },
            "migration_score": float(mig_score),
            "decay_state": state,
            "next_review_ts": next_review_ts,
            "notes": "WO-92 τ enforcement: decay state + next review derived deterministically from last_seen and half-life.",
        }
        _append_jsonl(args.events_ledger, ev)
        items.append(ev)

        if state in ("RISING", "FADING"):
            for task_kind in ("INCREASE_DOMAIN_DIVERSITY", "ADD_PRIMARY_ANCHORS"):
                tid = f"aal_tau_{task_kind.lower()}_{abs(hash((term, task_kind, args.run_id))) % (10**10)}"
                task_event(
                    ledger=args.task_ledger,
                    run_id=args.run_id,
                    task_id=tid,
                    status="QUEUED",
                    mode="AALMANAC_TAU",
                    claim_id="",
                    term=term,
                    task_kind=task_kind,
                    detail=f"WO-92 τ: term={term} state={state} mig={mig_score:.2f} age_days={age_days:.1f}",
                    artifacts={"tau_event": ev, "front_tags": ["AALMANAC_DECAY", state]},
                )

    out_obj = {
        "version": "aalmanac_tau_state.v0.1",
        "ts": _utc_now_iso(),
        "run_id": args.run_id,
        "n_terms": len(items),
        "items": items,
        "notes": "Materialized τ state for AAlmanac terms.",
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join(
        "out/reports", f"aalmanac_tau_state_{stamp}.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)
    print(f"[AAL_TAU] wrote: {out_path} terms={len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
