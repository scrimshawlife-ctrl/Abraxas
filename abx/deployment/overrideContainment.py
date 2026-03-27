from __future__ import annotations

from abx.deployment.types import DeploymentDriftRecord, EnvironmentOverrideRecord



def build_environment_overrides() -> list[EnvironmentOverrideRecord]:
    return [
        EnvironmentOverrideRecord(
            override_id="override.dev.debug-sampling",
            environment="dev",
            target_key="observability.sample_rate",
            precedence=20,
            containment="bounded",
        ),
        EnvironmentOverrideRecord(
            override_id="override.local.policy-bypass",
            environment="local",
            target_key="env.override.policy_bypass",
            precedence=90,
            containment="risk",
        ),
    ]



def override_precedence_summary() -> list[dict[str, object]]:
    rows = [x.__dict__ for x in build_environment_overrides()]
    return sorted(rows, key=lambda row: (row["environment"], -int(row["precedence"]), row["override_id"]))



def detect_hidden_semantic_drift() -> list[DeploymentDriftRecord]:
    out: list[DeploymentDriftRecord] = []
    for x in build_environment_overrides():
        if x.target_key.endswith("policy_bypass") or x.containment == "risk":
            out.append(
                DeploymentDriftRecord(
                    drift_id=f"drift.{x.override_id}",
                    category="config-policy-drift",
                    severity="high",
                    message=f"override {x.override_id} may bypass canonical policy",
                )
            )
    return out
