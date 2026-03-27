from __future__ import annotations

from abx.governance.types import SourceOfTruthRecord


AUTHORITY_MAP = [
    SourceOfTruthRecord(
        domain="runtime_frame",
        authoritative_surface="abx.resonance_frame.ResonanceFrame.v1",
        derived_surfaces=["abx.resonance_frame.FrameProjection.v1", "abx.frame_adapters.adapter_audit"],
        adapted_surfaces=["abx.frame_adapters.assemble_resonance_frame"],
        deprecated_surfaces=[],
    ),
    SourceOfTruthRecord(
        domain="contracts_registry",
        authoritative_surface="abx.rune_contracts + abx.rune_governance",
        derived_surfaces=["scripts/run_rune_governance_checks.py"],
        adapted_surfaces=[],
        deprecated_surfaces=[],
    ),
    SourceOfTruthRecord(
        domain="validation_proof_closure",
        authoritative_surface="abx.simulation_validation + abx.proof_chain + abx.closure_summary",
        derived_surfaces=["abx.operator_console.inspect-proof-chain"],
        adapted_surfaces=["abx.promotion_pack"],
        deprecated_surfaces=[],
    ),
    SourceOfTruthRecord(
        domain="portfolio_state",
        authoritative_surface="abx.paper_trading.PortfolioState",
        derived_surfaces=["abx.operator_console.inspect-portfolio"],
        adapted_surfaces=["abx.simulation_loop.strategy artifacts"],
        deprecated_surfaces=[],
    ),
    SourceOfTruthRecord(
        domain="lifecycle_promotion",
        authoritative_surface="abx.lifecycle_policy + abx.promotion_pack",
        derived_surfaces=["scripts/run_promotion_pack.py"],
        adapted_surfaces=["abx.operator_workflows.inspect-promotion-pack-workflow"],
        deprecated_surfaces=[],
    ),
    SourceOfTruthRecord(
        domain="continuity",
        authoritative_surface="abx.continuity.ContinuitySummaryArtifact.v1",
        derived_surfaces=["abx.operator_workflows.inspect-continuity"],
        adapted_surfaces=[],
        deprecated_surfaces=[],
    ),
]


def build_source_of_truth_report() -> dict[str, object]:
    rows = sorted(AUTHORITY_MAP, key=lambda x: x.domain)
    return {
        "artifactType": "SourceOfTruthReport.v1",
        "artifactId": "source-of-truth-abx",
        "domains": [row.__dict__ for row in rows],
    }


def check_derived_surface_misuse(*, domain: str, asserted_authority: str) -> dict[str, object]:
    table = {row.domain: row for row in AUTHORITY_MAP}
    row = table.get(domain)
    if row is None:
        return {
            "status": "NOT_COMPUTABLE",
            "issues": [f"unknown-domain:{domain}"],
        }

    if asserted_authority == row.authoritative_surface:
        return {"status": "VALID", "issues": []}

    issues: list[str] = []
    if asserted_authority in row.derived_surfaces:
        issues.append("derived-surface-used-as-authority")
    elif asserted_authority in row.adapted_surfaces:
        issues.append("adapted-surface-used-as-authority")
    elif asserted_authority in row.deprecated_surfaces:
        issues.append("deprecated-surface-used-as-authority")
    else:
        issues.append("unregistered-authority-surface")

    return {"status": "BROKEN", "issues": issues, "expected": row.authoritative_surface}
