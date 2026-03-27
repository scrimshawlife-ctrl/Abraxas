from __future__ import annotations

from abx.deployment.types import SecretBoundaryRecord



def build_secret_boundaries() -> list[SecretBoundaryRecord]:
    return [
        SecretBoundaryRecord(
            secret_id="secret.runtime.token",
            boundary="runtime-auth",
            source="secret.manager",
            semantic_risk="operational-only",
        ),
        SecretBoundaryRecord(
            secret_id="secret.connector.key",
            boundary="boundary-connector",
            source="secret.manager",
            semantic_risk="adapted-risk",
        ),
    ]
