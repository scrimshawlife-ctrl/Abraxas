from __future__ import annotations

from abx.continuity.types import PersistedIntentRecord


def build_intent_inventory() -> list[PersistedIntentRecord]:
    rows = [
        PersistedIntentRecord("intent.governance-closure", "mission.governance-closure", "ACTIVE_INTENT", "FRESH", False),
        PersistedIntentRecord("intent.bounded-agency", "mission.bounded-agency", "RESUMABLE_INTENT", "FRESH", True),
        PersistedIntentRecord("intent.concurrent-arbitration", "mission.concurrent-arbitration", "LATENT_INTENT", "FRESH", True),
        PersistedIntentRecord("intent.wave6-legacy", "mission.wave6-legacy", "SUPERSEDED_INTENT", "STALE", False),
        PersistedIntentRecord("intent.ops-cleanup", "mission.ops-cleanup", "RETIRED_INTENT", "ARCHIVED", False),
    ]
    return sorted(rows, key=lambda x: x.intent_id)
