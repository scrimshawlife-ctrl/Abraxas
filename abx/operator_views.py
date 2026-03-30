from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from abx.operator_projection import build_operator_projection_summary
from abx.promotion_policy import evaluate_promotion_policy
from abx.promotion_readiness import evaluate_promotion_readiness
from scripts.run_release_readiness import run_release_readiness


@dataclass(frozen=True)
class RunSummaryView:
    run_id: str
    projection_summary: dict[str, Any]
    policy_state: str
    readiness_state: dict[str, str]
    federated_summary: dict[str, Any]
    execution_status: dict[str, Any]
    blockers: list[str] = field(default_factory=list)
    artifact_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunDiffSummary:
    run_a: str
    run_b: str
    changed_fields: list[str]
    policy_delta: dict[str, Any]
    readiness_delta: dict[str, Any]
    federated_delta: dict[str, Any]
    execution_delta: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReleaseReadinessView:
    run_id: str
    status: str
    blocking_issues: list[str]
    non_blocking_issues: list[str]
    checklist: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceView:
    run_id: str
    federated_evidence_state_summary: str
    remote_evidence_packet_count: int
    inconsistency_flag: bool
    manifest_validation_outcome: str
    origin: str
    packet_list: list[dict[str, Any]] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _execution_status(run_id: str, *, base_dir: Path) -> dict[str, Any]:
    path = base_dir / "out" / "attestation" / f"execution-attestation-{run_id}.json"
    payload = _load_json(path)
    if not payload:
        return {
            "status": "MISSING",
            "overall_status": "MISSING",
            "policy_decision_state": "UNKNOWN",
            "fail_reasons": [],
            "artifact": path.as_posix(),
        }
    policy_gate = payload.get("policy_gate", {}) if isinstance(payload.get("policy_gate", {}), dict) else {}
    fail_reasons = payload.get("fail_reasons", [])
    return {
        "status": "PRESENT",
        "overall_status": str(payload.get("overall_status", "UNKNOWN")),
        "policy_decision_state": str(policy_gate.get("decision_state", "UNKNOWN")),
        "fail_reasons": [str(v) for v in fail_reasons][:8] if isinstance(fail_reasons, list) else [],
        "artifact": path.as_posix(),
    }


def build_evidence_view(run_id: str, *, base_dir: Path = Path(".")) -> EvidenceView:
    readiness = evaluate_promotion_readiness(run_id, base_dir=base_dir)
    federated = readiness.federated_evidence if isinstance(readiness.federated_evidence, dict) else {}

    packet_list: list[dict[str, Any]] = []
    manifest_path = str(federated.get("remote_evidence_manifest", "")).strip()
    manifest_status = str(federated.get("remote_evidence_status", "NOT_DECLARED"))
    origin = str(federated.get("remote_evidence_origin", ""))
    if manifest_path:
        manifest_payload = _load_json(Path(manifest_path)) or {}
        packets = manifest_payload.get("packets", []) if isinstance(manifest_payload.get("packets", []), list) else []
        for packet in packets[:24]:
            if not isinstance(packet, dict):
                continue
            packet_list.append(
                {
                    "packet_id": str(packet.get("packet_id", "")),
                    "status": str(packet.get("status", "UNKNOWN")).upper(),
                    "observed_at": str(packet.get("observed_at", "")),
                    "source": str(packet.get("ref", "")),
                    "origin": str(packet.get("origin", origin)),
                }
            )

    return EvidenceView(
        run_id=run_id,
        federated_evidence_state_summary=str(federated.get("federated_evidence_state", "ABSENT")),
        remote_evidence_packet_count=int(federated.get("remote_evidence_packet_count", 0) or 0),
        inconsistency_flag=bool(federated.get("federated_inconsistency", False)),
        manifest_validation_outcome=manifest_status,
        origin=origin,
        packet_list=packet_list,
        blockers=[str(v) for v in federated.get("blockers", [])][:16] if isinstance(federated.get("blockers", []), list) else [],
    )


def build_run_summary(run_id: str, *, base_dir: Path = Path(".")) -> RunSummaryView:
    projection = build_operator_projection_summary(run_id, base_dir=base_dir).to_dict()
    readiness = evaluate_promotion_readiness(run_id, base_dir=base_dir)
    policy = evaluate_promotion_policy(run_id, base_dir=base_dir, readiness_result=readiness)
    evidence = build_evidence_view(run_id, base_dir=base_dir)
    execution = _execution_status(run_id, base_dir=base_dir)

    blockers = sorted(
        set(
            [str(v) for v in readiness.warnings]
            + [str(v) for v in policy.blockers]
            + [str(v) for v in evidence.blockers]
            + [str(v) for v in execution.get("fail_reasons", [])]
        )
    )[:24]

    artifact_refs = [
        str(v)
        for v in [
            projection.get("artifacts", {}).get("validator", ""),
            projection.get("artifacts", {}).get("local_attestation", ""),
            projection.get("artifacts", {}).get("promotion_attestation", ""),
            policy.artifacts.get("waiver", ""),
            execution.get("artifact", ""),
            readiness.artifacts.get("promotion_attestation", ""),
            str((readiness.federated_evidence or {}).get("remote_evidence_manifest", "")),
        ]
        if str(v).strip()
    ]

    return RunSummaryView(
        run_id=run_id,
        projection_summary=projection,
        policy_state=policy.decision_state.value,
        readiness_state={
            "status": readiness.status.value,
            "local_promotion_state": readiness.local_promotion_state.value,
            "federated_readiness_state": readiness.federated_readiness_state.value,
        },
        federated_summary={
            "federated_evidence_state_summary": evidence.federated_evidence_state_summary,
            "remote_evidence_packet_count": evidence.remote_evidence_packet_count,
            "inconsistency_flag": evidence.inconsistency_flag,
            "manifest_validation_outcome": evidence.manifest_validation_outcome,
        },
        execution_status=execution,
        blockers=blockers,
        artifact_refs=artifact_refs[:12],
    )


def compare_runs(run_a: str, run_b: str, *, base_dir: Path = Path(".")) -> RunDiffSummary:
    a = build_run_summary(run_a, base_dir=base_dir).to_dict()
    b = build_run_summary(run_b, base_dir=base_dir).to_dict()

    changed_fields: list[str] = []
    for key in ["policy_state", "readiness_state", "federated_summary", "execution_status", "blockers"]:
        if a.get(key) != b.get(key):
            changed_fields.append(key)

    a_blockers = set(str(v) for v in a.get("blockers", []))
    b_blockers = set(str(v) for v in b.get("blockers", []))

    return RunDiffSummary(
        run_a=run_a,
        run_b=run_b,
        changed_fields=changed_fields,
        policy_delta={
            "from": a.get("policy_state", "UNKNOWN"),
            "to": b.get("policy_state", "UNKNOWN"),
        },
        readiness_delta={
            "from": a.get("readiness_state", {}),
            "to": b.get("readiness_state", {}),
        },
        federated_delta={
            "from": a.get("federated_summary", {}),
            "to": b.get("federated_summary", {}),
            "new_blockers": sorted(b_blockers - a_blockers),
            "cleared_blockers": sorted(a_blockers - b_blockers),
        },
        execution_delta={
            "from": a.get("execution_status", {}),
            "to": b.get("execution_status", {}),
        },
    )


def build_release_view(run_id: str, *, base_dir: Path = Path(".")) -> ReleaseReadinessView:
    release_path = base_dir / "out" / "release" / f"release-readiness-{run_id}.json"
    report = _load_json(release_path)
    if report is None:
        report = run_release_readiness(run_id, base_dir=base_dir)

    checks_raw = report.get("checks", []) if isinstance(report.get("checks", []), list) else []
    checklist = []
    for item in checks_raw[:24]:
        if not isinstance(item, dict):
            continue
        checklist.append(
            {
                "name": str(item.get("name", "unknown")),
                "outcome": str(item.get("outcome", "UNKNOWN")),
                "ok": bool(item.get("ok", False)),
                "notes": str(item.get("notes", ""))[:240],
            }
        )

    return ReleaseReadinessView(
        run_id=run_id,
        status=str(report.get("status", "NOT_READY")),
        blocking_issues=[str(v) for v in report.get("blocking_failures", [])][:16]
        if isinstance(report.get("blocking_failures", []), list)
        else [],
        non_blocking_issues=[str(v) for v in report.get("known_non_blocking", [])][:16]
        if isinstance(report.get("known_non_blocking", []), list)
        else [],
        checklist=checklist,
    )
