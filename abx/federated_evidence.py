from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from abx.federated_transport import RemoteEvidenceStatus, verify_remote_evidence_manifest


@dataclass(frozen=True)
class FederatedEvidence:
    external_attestation_refs: list[str] = field(default_factory=list)
    federated_ledger_ids: list[str] = field(default_factory=list)
    remote_validation_status: str = "UNAVAILABLE"
    remote_attestation_status: str = "UNAVAILABLE"
    remote_evidence_status: str = "NOT_DECLARED"
    remote_evidence_manifest: str = ""
    remote_evidence_manifest_id: str = ""
    remote_evidence_manifest_schema: str = ""
    remote_evidence_origin: str = ""
    remote_evidence_run_id: str = ""
    remote_evidence_packet_ids: list[str] = field(default_factory=list)
    remote_evidence_packet_count: int = 0
    remote_evidence_valid_packet_count: int = 0
    remote_evidence_invalid_packet_count: int = 0
    remote_evidence_stale_packet_count: int = 0
    federated_inconsistency: bool = False
    federated_evidence_state: str = "ABSENT"
    evidence_present: bool = False
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_confirmed(status: str) -> bool:
    return status.upper() in {"VALID", "PASS", "SUCCESS"}


def extract_federated_evidence(
    promotion_payload: dict[str, Any] | None,
    *,
    base_dir: Path = Path("."),
) -> FederatedEvidence:
    if not isinstance(promotion_payload, dict):
        return FederatedEvidence(
            blockers=["promotion_attestation_missing"],
        )

    federated = promotion_payload.get("federated", {}) if isinstance(promotion_payload.get("federated", {}), dict) else {}

    external_refs_raw = federated.get("external_attestation_refs", promotion_payload.get("external_attestation_refs", []))
    ledger_ids_raw = federated.get("federated_ledger_ids", promotion_payload.get("federated_ledger_ids", []))

    external_refs = [str(v) for v in external_refs_raw] if isinstance(external_refs_raw, list) else []
    ledger_ids = [str(v) for v in ledger_ids_raw] if isinstance(ledger_ids_raw, list) else []

    remote_validation_status = str(
        federated.get("remote_validation_status", promotion_payload.get("remote_validation_status", "UNAVAILABLE"))
    )
    remote_attestation_status = str(
        federated.get("remote_attestation_status", promotion_payload.get("remote_attestation_status", "UNAVAILABLE"))
    )

    manifest_ref = str(federated.get("remote_evidence_manifest", promotion_payload.get("remote_evidence_manifest", "")))
    remote_evidence = verify_remote_evidence_manifest(manifest_ref or None, base_dir=base_dir)

    evidence_present = bool(external_refs or ledger_ids or remote_evidence.packet_ids)
    blockers: list[str] = []

    if not evidence_present:
        blockers.append("missing_external_attestation_refs_and_federated_ledger_ids")

    if not _is_confirmed(remote_validation_status):
        blockers.append("remote_validation_not_confirmed")
    if not _is_confirmed(remote_attestation_status):
        blockers.append("remote_attestation_not_confirmed")

    federated_state = "ABSENT"
    if remote_evidence.status == RemoteEvidenceStatus.MISSING:
        federated_state = "PARTIAL"
        blockers.append("remote_evidence_manifest_missing")
    elif remote_evidence.status == RemoteEvidenceStatus.MALFORMED:
        federated_state = "MALFORMED"
        blockers.append("remote_evidence_manifest_malformed")
        blockers.extend(remote_evidence.errors)
    elif remote_evidence.status == RemoteEvidenceStatus.INCONSISTENT:
        federated_state = "INCONSISTENT"
        blockers.append("remote_evidence_inconsistent")
    elif remote_evidence.status == RemoteEvidenceStatus.STALE:
        federated_state = "STALE"
        blockers.append("remote_evidence_stale")
    elif remote_evidence.status == RemoteEvidenceStatus.PARTIAL:
        federated_state = "PARTIAL"
        blockers.append("remote_evidence_partial")
    elif remote_evidence.status == RemoteEvidenceStatus.VALID:
        federated_state = "VALID"

    if federated_state == "ABSENT" and evidence_present:
        federated_state = "PARTIAL"

    if (
        federated_state == "VALID"
        and (not _is_confirmed(remote_validation_status) or not _is_confirmed(remote_attestation_status))
    ):
        federated_state = "PARTIAL"

    return FederatedEvidence(
        external_attestation_refs=external_refs,
        federated_ledger_ids=ledger_ids,
        remote_validation_status=remote_validation_status,
        remote_attestation_status=remote_attestation_status,
        remote_evidence_status=remote_evidence.status.value,
        remote_evidence_manifest=remote_evidence.manifest_path,
        remote_evidence_manifest_id=remote_evidence.manifest_id,
        remote_evidence_manifest_schema=remote_evidence.manifest_schema,
        remote_evidence_origin=remote_evidence.origin,
        remote_evidence_run_id=remote_evidence.run_id,
        remote_evidence_packet_ids=remote_evidence.packet_ids,
        remote_evidence_packet_count=remote_evidence.packet_count,
        remote_evidence_valid_packet_count=remote_evidence.valid_packet_count,
        remote_evidence_invalid_packet_count=remote_evidence.invalid_packet_count,
        remote_evidence_stale_packet_count=remote_evidence.stale_packet_count,
        federated_inconsistency=remote_evidence.inconsistent,
        federated_evidence_state=federated_state,
        evidence_present=evidence_present,
        blockers=sorted(set(blockers)),
    )
