from __future__ import annotations

from typing import Any

from abraxas.canary.rollback_packet_models import AUTHORITY_FLAGS


def validate_rollback_packet_run(run: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if run.get("artifact") != "CANARY-ROLLBACK-PACKET-001":
        errors.append("artifact_mismatch")
    if run.get("schema_version") != "CanaryRollbackPacketRun.v1":
        errors.append("schema_version_mismatch")
    if run.get("authority") != AUTHORITY_FLAGS:
        errors.append("authority_mismatch")
    counts = run.get("counts") if isinstance(run.get("counts"), dict) else {}
    packets = run.get("packets") if isinstance(run.get("packets"), list) else []
    skipped = run.get("skipped_recommendations") if isinstance(run.get("skipped_recommendations"), list) else []
    if counts.get("packets_created") != len(packets):
        errors.append("packets_count_mismatch")
    if counts.get("skipped") != len(skipped):
        errors.append("skipped_count_mismatch")
    return errors
