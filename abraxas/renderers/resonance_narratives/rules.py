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
        # Likely oracle-ish / v2-ish locations
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

