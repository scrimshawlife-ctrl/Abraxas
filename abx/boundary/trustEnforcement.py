from __future__ import annotations

from abx.boundary.errorTaxonomy import make_error
from abx.boundary.types import BoundaryValidationResult, InputEnvelope, TrustClassificationRecord


_ALLOWED_AUTHORITATIVE = {"AUTHORITATIVE_INTERNAL", "GOVERNED_DERIVED"}


def classify_trust_record(envelope: InputEnvelope) -> TrustClassificationRecord:
    rationale = {
        "AUTHORITATIVE_INTERNAL": "internal namespace",
        "GOVERNED_DERIVED": "governed derived source",
        "EXTERNAL_ASSERTED": "external input requires degradation path",
        "UNTRUSTED": "explicit untrusted input",
        "UNKNOWN": "unmapped source",
        "NOT_COMPUTABLE": "trust classification unavailable",
    }.get(envelope.trust_state, "unrecognized trust state")
    return TrustClassificationRecord(envelope_id=envelope.envelope_id, trust_state=envelope.trust_state, rationale=rationale)


def enforce_trust_for_authoritative_mutation(envelope: InputEnvelope) -> BoundaryValidationResult:
    trust = classify_trust_record(envelope)
    if trust.trust_state in _ALLOWED_AUTHORITATIVE:
        return BoundaryValidationResult(envelope_id=envelope.envelope_id, status="ACCEPTED", state="VALID", accepted=True, errors=[])
    if trust.trust_state == "EXTERNAL_ASSERTED":
        return BoundaryValidationResult(
            envelope_id=envelope.envelope_id,
            status="DEGRADED",
            state="VALID",
            accepted=False,
            errors=[make_error("BOUNDARY_UNTRUSTED", "external asserted cannot mutate authoritative surface")],
        )
    return BoundaryValidationResult(
        envelope_id=envelope.envelope_id,
        status="REJECTED",
        state="MALFORMED",
        accepted=False,
        errors=[make_error("BOUNDARY_REJECTED", f"trust_state={trust.trust_state} blocked")],
    )
