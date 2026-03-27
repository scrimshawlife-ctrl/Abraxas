from __future__ import annotations

from abx.boundary.errorTaxonomy import make_error
from abx.boundary.inputClassification import classify_input_state
from abx.boundary.trustModel import is_valid_trust_state
from abx.boundary.types import BoundaryValidationResult, InputEnvelope


def validate_envelope(envelope: InputEnvelope, *, current_tick: int, stale_after_ticks: int = 5) -> BoundaryValidationResult:
    errors = []
    if not isinstance(envelope.payload, dict):
        errors.append(make_error("BOUNDARY_MALFORMED", "payload must be object"))
    if not envelope.interface_id.strip():
        errors.append(make_error("BOUNDARY_MALFORMED", "interface_id required"))
    if not is_valid_trust_state(envelope.trust_state):
        errors.append(make_error("BOUNDARY_UNKNOWN_TRUST", "unknown trust state"))

    state = classify_input_state(envelope, current_tick=current_tick, stale_after_ticks=stale_after_ticks)
    if state == "PARTIAL":
        errors.append(make_error("BOUNDARY_PARTIAL", "required keys missing"))
    if state == "STALE":
        errors.append(make_error("BOUNDARY_STALE", "input stale"))

    accepted = state == "VALID" and not errors
    status = "ACCEPTED" if accepted else ("DEGRADED" if state in {"STALE", "PARTIAL"} else "REJECTED")
    return BoundaryValidationResult(
        envelope_id=envelope.envelope_id,
        status=status,
        state=state,
        accepted=accepted,
        errors=errors,
    )
