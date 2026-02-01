from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import hashlib
import json
import time

from aal_core.aalmanac.scoring import priority_score
from aal_core.aalmanac.storage.entries import DEFAULT_ENTRIES_PATH, load_entries
from aal_core.aalmanac.storage.rejections import DEFAULT_REJECTIONS_PATH

DEFAULT_ORACLE_LEDGER_PATH = Path.home() / ".aal" / "ledger" / "aalmanac_oracle.jsonl"


def _sha256(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _write_ledger(record: Dict[str, Any], *, ledger_path: Optional[Path] = None) -> None:
    target = ledger_path or DEFAULT_ORACLE_LEDGER_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text("", encoding="utf-8")
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def _sorted_candidates(entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def sort_key(item: Dict[str, Any]) -> tuple:
        return (
            -priority_score(item),
            str(item.get("term_canonical", "")),
            str(item.get("entry_id", "")),
        )

    return sorted(entries, key=sort_key)


def build_oracle_attachment(
    entries: Iterable[Dict[str, Any]],
    *,
    run_id: str,
    top_single: int = 5,
    top_compound: int = 5,
    watchlist_threshold: float = 0.75,
    watchlist_delta_min: float = 0.15,
) -> Dict[str, Any]:
    entries_list = list(entries)
    singles = [e for e in entries_list if e.get("term_class") == "single"]
    compounds = [e for e in entries_list if e.get("term_class") in {"compound", "phrase"}]

    sorted_single = _sorted_candidates(singles)
    sorted_compound = _sorted_candidates(compounds)

    top_single_terms = [str(e.get("term_raw", "")) for e in sorted_single[:top_single] if e.get("term_raw")]
    top_compound_terms = [
        str(e.get("term_raw", "")) for e in sorted_compound[:top_compound] if e.get("term_raw")
    ]

    watchlist = []
    for entry in entries_list:
        drift = entry.get("drift", {}) or {}
        drift_charge = float(drift.get("drift_charge", 0.0) or 0.0)
        delta = float(drift.get("delta_from_prior", 0.0) or 0.0)
        if drift_charge >= watchlist_threshold and delta >= watchlist_delta_min:
            term = str(entry.get("term_raw", ""))
            if term:
                watchlist.append(term)

    total_new = sum(1 for e in entries_list if e.get("mutation_type") == "neologism")
    total_mutations = sum(1 for e in entries_list if e.get("mutation_type") != "neologism")
    drift_vals = [float((e.get("drift", {}) or {}).get("drift_charge", 0.0) or 0.0) for e in entries_list]
    mean_drift = sum(drift_vals) / len(drift_vals) if drift_vals else 0.0

    attachment = {
        "schema_version": "aal.aalmanac.oracle_attachment.v1",
        "run_id": run_id,
        "top_single": top_single_terms,
        "top_compound": top_compound_terms,
        "watchlist": watchlist,
        "meta": {
            "total_new": total_new,
            "total_mutations": total_mutations,
            "mean_drift_charge": mean_drift,
        },
        "rejections": {"total": 0, "reasons": {}},
    }
    return attachment


def build_oracle_attachment_with_rejections(
    entries: Iterable[Dict[str, Any]],
    rejections: Iterable[Dict[str, Any]],
    *,
    run_id: str = "unknown",
) -> Dict[str, Any]:
    attachment = build_oracle_attachment(entries, run_id=run_id)
    reasons: Dict[str, int] = {}
    total = 0
    for item in rejections:
        reason = str(item.get("reason", "unknown"))
        if reason:
            reasons[reason] = reasons.get(reason, 0) + 1
            total += 1
    attachment["rejections"] = {"total": total, "reasons": reasons}
    return attachment


def summarize_rejections(*, rejections_path: Optional[Path] = None) -> Dict[str, Any]:
    target = rejections_path or DEFAULT_REJECTIONS_PATH
    if not target.exists():
        return {"total": 0, "reasons": {}}
    total = 0
    reasons: Dict[str, int] = {}
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        reason = str(obj.get("rejected_reason", "unknown"))
        reasons[reason] = reasons.get(reason, 0) + 1
        total += 1
    return {"total": total, "reasons": reasons}


def build_oracle_attachment_from_storage(
    *,
    run_id: str,
    entries_path: Optional[Path] = None,
    ledger_path: Optional[Path] = None,
    rejections_path: Optional[Path] = None,
) -> Dict[str, Any]:
    entries = load_entries(entries_path=entries_path or DEFAULT_ENTRIES_PATH)
    attachment = build_oracle_attachment(entries, run_id=run_id)
    attachment["rejections"] = summarize_rejections(rejections_path=rejections_path)
    record = {
        "schema_version": "aal.aalmanac.oracle_record.v1",
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_id": run_id,
        "attachment": attachment,
        "attachment_hash": _sha256(attachment),
        "provenance": {
            "deterministic": True,
            "source": "aal_core.aalmanac.oracle_attachment",
            "entries_path": str(entries_path or DEFAULT_ENTRIES_PATH),
        },
    }
    _write_ledger(record, ledger_path=ledger_path)
    return attachment
