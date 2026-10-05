from __future__ import annotations

from dataclasses import dataclass
from typing import Set


@dataclass(frozen=True)
class NarrativeRules:
    """
    Hard constraints for the ResonanceNarratives renderer.

    - allowed_pointers: whitelist of JSON pointers that the renderer may reference.
      (Keep narrow; widen with governance as envelope fields stabilize.)
    - forbidden_tokens: soft rail against causal language unless you explicitly allow it.
    """

    allowed_pointers: Set[str]
    forbidden_tokens: Set[str]


def default_rules() -> NarrativeRules:
    # Start narrow. Expand with governance once envelope fields are stable.
    allowed = {
        "/artifact_id",
        "/created_at",
        "/input_hash",
        "/missing_inputs",
        "/not_computable",
        # Oracle signal layer (v1, v2, scores_v1)
        "/oracle_signal",
        "/oracle_signal/window",
        "/oracle_signal/scores_v1",
        "/oracle_signal/scores_v1/slang",
        "/oracle_signal/scores_v1/slang/top_vital",
        "/oracle_signal/scores_v1/slang/top_risk",
        "/oracle_signal/aalmanac",
        "/oracle_signal/aalmanac/top_patterns",
        "/oracle_signal/v2",
        "/oracle_signal/v2/mode",
        "/oracle_signal/v2/compliance",
        "/oracle_signal/v2/compliance/status",
        "/oracle_signal/v2/compliance/provenance",
        "/oracle_signal/meta",
        "/oracle_signal/evidence",
        # Likely oracle-ish / v2-ish locations (legacy)
        "/signal_layer",
        "/signal_layer/scores",
        "/symbolic_compression",
        "/symbolic_compression/motifs",
        "/symbolic_compression/clusters",
        "/interpretive_overlay",
        # Sample oracle run artifacts (data/oracle_runs_sample.jsonl)
        "/compression/signal_strengths",
        "/compression/compressed_tokens",
    }
    forbidden = {"because", "therefore", "this proves", "means that"}
    return NarrativeRules(allowed_pointers=allowed, forbidden_tokens=forbidden)


def pointer_is_allowed(pointer: str, rules: NarrativeRules) -> bool:
    # Allow exact match or descendant paths
    if pointer in rules.allowed_pointers:
        return True
    for base in rules.allowed_pointers:
        if pointer.startswith(base.rstrip("/") + "/"):
            return True
    return False


def violates_forbidden_tokens(text: str, rules: NarrativeRules) -> bool:
    t = text.lower()
    return any(tok in t for tok in rules.forbidden_tokens)

