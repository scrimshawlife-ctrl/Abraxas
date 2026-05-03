from __future__ import annotations

from typing import Any

from abraxas.semantic.contracts import ContractLoadError, canonical_hash, load_contract

INPUTS = {
    "oracle": ("out/oracle/oracle_input.latest.json", "OracleInput.v1"),
    "scoring": ("out/scoring/forecast_outcome_set.latest.json", "ForecastOutcomeSet.v1"),
    "canary": ("out/canary/canary_candidate_set.latest.json", "CanaryCandidateSet.v1"),
}


def build_semantic_lineage_report() -> dict[str, Any]:
    contracts: dict[str, dict[str, Any]] = {}
    contract_rows: list[dict[str, Any]] = []
    warnings: list[str] = []

    for name, (path, schema) in INPUTS.items():
        try:
            c = load_contract(path, schema)
        except ContractLoadError as exc:
            payload = {
                "schema_version": "SemanticLineageReport.v1",
                "status": "NOT_COMPUTABLE",
                "reason": f"{exc.reason}:{name}",
                "contracts": [],
                "links": [],
                "warnings": [],
                "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
            }
            payload["canonical_hash"] = canonical_hash(payload)
            return payload

        env = c.get("envelope") if isinstance(c.get("envelope"), dict) else None
        if env is None:
            warnings.append(f"missing_envelope:{name}")
        contracts[name] = c
        contract_rows.append(
            {
                "contract": name,
                "envelope_present": env is not None,
                "run_id": env.get("run_id") if env else None,
                "parent_run_id": env.get("parent_run_id") if env else None,
                "source_hashes": env.get("source_hashes", []) if env else [],
                "canonical_hash": c.get("canonical_hash"),
            }
        )

    run_ids = {r["run_id"] for r in contract_rows if r["run_id"]}
    links: list[dict[str, Any]] = []
    for row in contract_rows:
        parent = row.get("parent_run_id")
        if parent:
            ok = parent in run_ids
            links.append({"contract": row["contract"], "parent_run_id": parent, "valid": ok})
            if not ok:
                warnings.append(f"broken_parent_reference:{row['contract']}")
        elif row["envelope_present"]:
            warnings.append(f"orphan_contract:{row['contract']}")

    source_sets = {r["contract"]: set(r.get("source_hashes") or []) for r in contract_rows}
    names = list(source_sets.keys())
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            overlap = sorted(source_sets[a].intersection(source_sets[b]))
            if overlap:
                warnings.append(f"shared_source_hash_overlap:{a}:{b}:{len(overlap)}")

    report = {
        "schema_version": "SemanticLineageReport.v1",
        "status": "LINEAGE_REPORT_READY",
        "contracts": contract_rows,
        "links": links,
        "warnings": sorted(set(warnings)),
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
    }
    report["canonical_hash"] = canonical_hash(report)
    return report
