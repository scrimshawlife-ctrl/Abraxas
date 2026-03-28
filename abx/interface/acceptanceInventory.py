from __future__ import annotations


def build_acceptance_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("ac.001", "hf.001", "RECEIVED_UNACCEPTED", "receiver queued validation"),
        ("ac.002", "hf.002", "ACCEPTED_STRUCTURAL", "shape valid"),
        ("ac.003", "hf.003", "ACCEPTED_SEMANTIC", "meaning preserved"),
        ("ac.004", "hf.004", "ACCEPTED_APPLIED", "state applied"),
        ("ac.005", "hf.005", "REJECTED", "authority mismatch"),
        ("ac.006", "hf.006", "COERCED_DEFAULTED", "fields defaulted to parse"),
        ("ac.007", "hf.007", "INTERPRETATION_MISMATCH", "receiver interpretation diverged"),
        ("ac.008", "hf.008", "NOT_COMPUTABLE", "acceptance telemetry unavailable"),
    )
