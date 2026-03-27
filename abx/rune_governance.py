from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from abx.rune_contracts import ABXRuneContract, load_abx_rune_contracts


@dataclass(frozen=True)
class RuneGovernanceReport:
    duplicate_rune_ids: list[str] = field(default_factory=list)
    missing_contracts: list[str] = field(default_factory=list)
    dependency_mismatch: list[str] = field(default_factory=list)
    schema_drift: list[str] = field(default_factory=list)
    forbidden_influence_leakage: list[str] = field(default_factory=list)
    vector_enforcement_failures: list[str] = field(default_factory=list)
    ok: bool = False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def check_rune_governance(registry_path: Path | None = None) -> RuneGovernanceReport:
    contracts = load_abx_rune_contracts(registry_path)
    known_rune_ids = {contract.rune_id for contract in contracts}

    duplicate_rune_ids: list[str] = []
    seen: set[str] = set()
    for contract in contracts:
        if contract.rune_id in seen:
            duplicate_rune_ids.append(contract.rune_id)
        seen.add(contract.rune_id)

    missing_contracts = sorted(
        contract.rune_id
        for contract in contracts
        if not contract.inputs or not contract.outputs or not contract.provenance_fields
    )

    dependency_mismatch = sorted(
        f"{contract.rune_id}:{dep}"
        for contract in contracts
        for dep in contract.dependencies
        if dep not in known_rune_ids
    )

    schema_drift: list[str] = []
    registry_file = _repo_root() / "abraxas" / "runes" / "registry.json"
    if not registry_file.exists():
        schema_drift.append("missing:abraxas/runes/registry.json")

    forbidden_influence_leakage = sorted(
        contract.rune_id for contract in contracts if contract.influence_policy == "DIRECT"
    )

    vector_enforcement_failures = sorted(
        contract.rune_id
        for contract in contracts
        if contract.category == "INGEST" and "normalized_vector" not in " ".join(i.name for i in contract.inputs)
    )

    ok = not any(
        [
            duplicate_rune_ids,
            missing_contracts,
            dependency_mismatch,
            schema_drift,
            forbidden_influence_leakage,
        ]
    )
    return RuneGovernanceReport(
        duplicate_rune_ids=duplicate_rune_ids,
        missing_contracts=missing_contracts,
        dependency_mismatch=dependency_mismatch,
        schema_drift=schema_drift,
        forbidden_influence_leakage=forbidden_influence_leakage,
        vector_enforcement_failures=vector_enforcement_failures,
        ok=ok,
    )


def check_validation_artifact_traceability(payload: dict) -> list[str]:
    issues: list[str] = []
    run_id = str(payload.get("runId") or "")
    artifact_id = str(payload.get("artifactId") or "")
    correlation = payload.get("correlation") if isinstance(payload.get("correlation"), dict) else {}
    ledger_ids = correlation.get("ledgerIds") if isinstance(correlation.get("ledgerIds"), list) else []
    validated = payload.get("validatedArtifacts") if isinstance(payload.get("validatedArtifacts"), list) else []

    if not run_id:
        issues.append("missing-runId")
    if not artifact_id:
        issues.append("missing-artifactId")
    if not ledger_ids:
        issues.append("missing-ledgerIds")
    if not validated:
        issues.append("missing-validatedArtifacts")

    return sorted(issues)
