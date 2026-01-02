from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional


DriftClass = Literal["none", "render", "canon", "nondeterminism", "unknown"]


@dataclass(frozen=True)
class DriftDiagnosis:
    drift_class: DriftClass
    reason: str


def classify_drift(
    *,
    invariance_report: Dict[str, Any],
    expected_session_ledger_hash: Optional[str],
    actual_session_ledger_hash: Optional[str],
) -> DriftDiagnosis:
    """
    Heuristic classifier, deterministic.

    Principles:
      - If invariance_report says canon_invariant True, but ledger hash differs => render drift or ledger format drift.
      - If invariance_report says canon_invariant False => canon drift (or nondeterminism if multiple hashes inside).
      - If invariance report includes multiple unique hashes across runs => nondeterminism.
    """
    if not expected_session_ledger_hash:
        return DriftDiagnosis(drift_class="unknown", reason="No golden ledger hash pinned; cannot classify by hash.")

    if expected_session_ledger_hash == actual_session_ledger_hash:
        return DriftDiagnosis(drift_class="none", reason="Pinned session_ledger hash matches.")

    canon_invariant = bool(invariance_report.get("canon_invariant"))
    drift_class_reported = str(invariance_report.get("drift_class", "unknown"))

    # Detect nondeterminism via unique hashes in report if present
    dsp_hashes = invariance_report.get("dsp_hashes") or []
    fusion_hashes = invariance_report.get("fusion_hashes") or []
    try:
        dsp_unique = len(set(dsp_hashes)) if isinstance(dsp_hashes, list) else 0
        fusion_unique = len(set(fusion_hashes)) if isinstance(fusion_hashes, list) else 0
    except Exception:
        dsp_unique = 0
        fusion_unique = 0

    if (dsp_unique and dsp_unique > 1) or (fusion_unique and fusion_unique > 1):
        return DriftDiagnosis(
            drift_class="nondeterminism",
            reason=f"Multiple unique hashes across runs (dsp_unique={dsp_unique}, fusion_unique={fusion_unique}).",
        )

    if canon_invariant:
        # Canon invariant but ledger hash changed: likely render/manifest/ordering/format change
        return DriftDiagnosis(
            drift_class="render",
            reason="Invariance report indicates canon invariant, but ledger hash differs (likely render/ledger format drift).",
        )

    if drift_class_reported == "canon":
        return DriftDiagnosis(
            drift_class="canon",
            reason="Invariance report indicates canon drift.",
        )

    return DriftDiagnosis(
        drift_class="unknown",
        reason="Mismatch without clear signal; inspect invariance_report + session_ledger diffs.",
    )

