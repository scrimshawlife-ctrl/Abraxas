from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import hashlib
import json
import time

LEDGER_PATH = Path.home() / ".aal" / "neon_genie" / "neon_genie.jsonl"

_ALLOWED_TYPES = {
    "net_new_application",
    "system_adjacent_tool",
    "upgrade_proposal",
}


def _sha256(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _mean(values: Iterable[float]) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else 0.0


def _drift_lookup(entries: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for entry in entries:
        term = str(entry.get("term_canonical", ""))
        drift = float((entry.get("drift", {}) or {}).get("drift_charge", 0.0) or 0.0)
        if term:
            out[term] = drift
    return out


def _gate_drift_density(entries: Iterable[Dict[str, Any]], *, threshold: float, min_count: int) -> bool:
    count = 0
    for entry in entries:
        drift_charge = float((entry.get("drift", {}) or {}).get("drift_charge", 0.0) or 0.0)
        if drift_charge >= threshold:
            count += 1
            if count >= min_count:
                return True
    return False


def _gate_cross_domain(memetic_domains: Iterable[str], semiotic_domains: Iterable[str], *, min_overlap: int) -> bool:
    mem = {str(d) for d in memetic_domains if d}
    sem = {str(d) for d in semiotic_domains if d}
    return len(mem.intersection(sem)) >= min_overlap


def _gate_unserved_vector(unserved_vector: bool) -> bool:
    return bool(unserved_vector)


def _pressure_alignment(source_terms: Iterable[str], drift_map: Dict[str, float]) -> float:
    values = []
    for term in source_terms:
        key = str(term).strip().lower()
        if not key:
            continue
        values.append(drift_map.get(key, 0.0))
    return _mean(values)


def _normalize_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    kind = str(candidate.get("type", ""))
    if kind not in _ALLOWED_TYPES:
        kind = "upgrade_proposal"
    return {
        "type": kind,
        "name": str(candidate.get("name", "")),
        "description": str(candidate.get("description", "")),
        "source_terms": [str(t).lower() for t in candidate.get("source_terms", []) if t],
        "novelty_delta": float(candidate.get("novelty_delta", 0.0) or 0.0),
        "buildability": bool(candidate.get("buildability", False)),
        "system_non_overlap": bool(candidate.get("system_non_overlap", False)),
        "build_vector": list(candidate.get("build_vector", [])),
    }


def _passes_promotion(candidate: Dict[str, Any], *, pressure_alignment: float) -> bool:
    return (
        float(candidate.get("novelty_delta", 0.0) or 0.0) >= 0.65
        and pressure_alignment >= 0.70
        and bool(candidate.get("buildability", False))
        and bool(candidate.get("system_non_overlap", False))
    )


def build_neon_genie_signal(
    *,
    run_id: str,
    aalmanac_entries: Iterable[Dict[str, Any]],
    memetic_domains: Iterable[str],
    semiotic_domains: Iterable[str],
    unserved_vector: bool,
    candidates: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    entries_list = list(aalmanac_entries)
    drift_gate = _gate_drift_density(entries_list, threshold=0.75, min_count=2)
    domain_gate = _gate_cross_domain(memetic_domains, semiotic_domains, min_overlap=2)
    vector_gate = _gate_unserved_vector(unserved_vector)

    gates = {
        "drift_density": drift_gate,
        "cross_domain_tension": domain_gate,
        "unserved_vector": vector_gate,
    }

    drift_map = _drift_lookup(entries_list)
    normalized = [_normalize_candidate(c) for c in candidates]

    outputs: List[Dict[str, Any]] = []
    for cand in normalized:
        alignment = _pressure_alignment(cand["source_terms"], drift_map)
        cand["pressure_alignment"] = alignment
        cand["passes_promotion"] = _passes_promotion(cand, pressure_alignment=alignment)
        if all(gates.values()) and cand["passes_promotion"]:
            outputs.append(cand)

    signal = {
        "schema_version": "aal.neon_genie.signal.v1",
        "run_id": run_id,
        "gates": gates,
        "source_pressures": [
            {"term": term, "drift_charge": drift}
            for term, drift in sorted(drift_map.items(), key=lambda x: -x[1])[:6]
        ],
        "outputs": outputs,
        "meta": {
            "output_count": len(outputs),
            "candidate_count": len(normalized),
        },
        "provenance": {
            "deterministic": True,
            "generator": "aal_core.neon_genie.pipeline",
        },
    }

    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **signal}, sort_keys=True) + "\n")

    return signal


def load_latest_signal(*, ledger_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    path = ledger_path or LEDGER_PATH
    if not path.exists():
        return None
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return None
