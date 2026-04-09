from __future__ import annotations

from typing import Mapping, Sequence

from abraxas.contracts.oracle_validator_summary_v1 import OracleValidatorSummaryV1


def build_validator_summary_v2(
    *,
    output: Mapping[str, object],
    hashes: Mapping[str, str],
    artifact_refs: Sequence[str],
) -> dict:
    not_computable = sorted(
        [
            str(x.get("attachment_id"))
            for x in (output.get("advisory_attachments") or [])
            if x.get("status") == "NOT_COMPUTABLE" or x.get("computable") is False
        ]
    )
    overall_computable = bool((output.get("provenance") or {}).get("computable", True))
    summary = OracleValidatorSummaryV1(
        run_id=str(output.get("run_id")),
        lane=str(output.get("lane")),
        status="PASS" if bool(output.get("authority_advisory_boundary_enforced")) and overall_computable else "BLOCKED",
        authority_item_count=len((output.get("authority") or {}).get("signal_items") or []),
        advisory_attachment_count=len(output.get("advisory_attachments") or []),
        not_computable_attachments=not_computable,
        artifact_refs=list(artifact_refs),
        hashes=dict(hashes),
    )
    return summary.to_dict()
