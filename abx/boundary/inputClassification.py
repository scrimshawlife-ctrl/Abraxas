from __future__ import annotations

from abx.boundary.types import InputEnvelope


def classify_input_state(envelope: InputEnvelope, *, current_tick: int, stale_after_ticks: int = 5) -> str:
    if not isinstance(envelope.payload, dict):
        return "MALFORMED"
    if envelope.received_tick < 0:
        return "MALFORMED"
    missing = [key for key in ("run_id", "scenario_id") if key not in envelope.payload]
    if missing:
        return "PARTIAL"
    if current_tick - envelope.received_tick > stale_after_ticks:
        return "STALE"
    return "VALID"
