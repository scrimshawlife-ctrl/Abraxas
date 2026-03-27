from __future__ import annotations


def classify_persistence_state(*, persistence_state: str, freshness_state: str, revalidation_required: bool) -> str:
    if persistence_state == "ACTIVE_INTENT" and freshness_state == "FRESH" and not revalidation_required:
        return "ACTIVE_INTENT"
    if persistence_state == "LATENT_INTENT":
        return "LATENT_INTENT"
    if persistence_state == "RESUMABLE_INTENT" and revalidation_required:
        return "RESUMABLE_INTENT"
    if freshness_state == "STALE":
        return "STALE_INTENT"
    if persistence_state == "SUPERSEDED_INTENT":
        return "SUPERSEDED_INTENT"
    if persistence_state == "RETIRED_INTENT":
        return "RETIRED_INTENT"
    return "NOT_COMPUTABLE"
