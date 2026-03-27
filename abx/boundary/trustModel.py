from __future__ import annotations

TRUST_STATES = {
    "AUTHORITATIVE_INTERNAL",
    "GOVERNED_DERIVED",
    "EXTERNAL_ASSERTED",
    "UNTRUSTED",
    "UNKNOWN",
    "NOT_COMPUTABLE",
}


def classify_trust_from_source(source: str) -> tuple[str, str]:
    src = source.strip().lower()
    if src.startswith("internal"):
        return "AUTHORITATIVE_INTERNAL", "internal source namespace"
    if src.startswith("governed"):
        return "GOVERNED_DERIVED", "governed derivative feed"
    if src.startswith("external"):
        return "EXTERNAL_ASSERTED", "external assertion requires policy gate"
    if src.startswith("untrusted"):
        return "UNTRUSTED", "explicit untrusted source"
    return "UNKNOWN", "source not mapped"


def is_valid_trust_state(trust_state: str) -> bool:
    return trust_state in TRUST_STATES
