from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from abraxas.oracle.v2.orchestrate import attach_v2
from abraxas.oracle.v2.render import render_by_mode
from abraxas.oracle.v2.export import export_run, compute_run_id
from abraxas.oracle.v2.evidence_convention import attach_evidence_from_run_dir


def run_bundle(
    *,
    envelope: Dict[str, Any],
    config_hash: str,
    out_dir: str = "out",
    thresholds: Dict[str, float] | None = None,
    user_mode_request: str | None = None,
    do_stabilization_tick: bool = True,
    evidence_budget_bytes: int | None = None,
    config_payload: Dict[str, Any] | None = None,
    config_source: str | None = None,
    ledger_path: str | None = None,
    date_iso: str | None = None,
    validate: bool = True,
    # evidence attach (optional): mapping evidence_key -> filename in out/<run_id>/evidence/
    attach_evidence_files: Mapping[str, str] | None = None,
    compute_evidence_hashes: bool = True,
) -> Dict[str, Any]:
    """
    One-call v2 shim runner:
      1) attach v2 (optionally ledger tick, validation)
      2) render by locked mode (evidence-gated)
      3) export artifacts (surface/envelope/manifest)
      4) optionally attach evidence pointers from run dir (only existing files)

    Returns:
      { "run_id": str, "manifest": dict, "surface": dict }
    """
    attach_v2(
        envelope=envelope,
        config_hash=config_hash,
        thresholds=thresholds,
        user_mode_request=user_mode_request,
        do_stabilization_tick=do_stabilization_tick,
        evidence_budget_bytes=evidence_budget_bytes,
        config_payload=config_payload,
        config_source=config_source,
        ledger_path=ledger_path,
        date_iso=date_iso,
        validate=validate,
    )

    # run_id becomes stable once v2 block exists
    run_id = compute_run_id(envelope)

    if attach_evidence_files:
        attach_evidence_from_run_dir(
            envelope=envelope,
            out_dir=out_dir,
            files=dict(attach_evidence_files),
            compute_hashes=compute_evidence_hashes,
        )

    surface = render_by_mode(envelope)
    manifest = export_run(envelope=envelope, surface=surface, out_dir=out_dir)

    return {"run_id": run_id, "manifest": manifest, "surface": surface}
