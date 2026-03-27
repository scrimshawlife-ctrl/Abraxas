from __future__ import annotations

from abx.deployment.types import EnvironmentParityRecord



def build_environment_parity_records() -> list[EnvironmentParityRecord]:
    return [
        EnvironmentParityRecord(
            environment="dev",
            baseline_environment="prod",
            parity_status="controlled-adaptation",
            differences=["reduced_retries", "debug_sampling_enabled"],
            owner="engineering",
        ),
        EnvironmentParityRecord(
            environment="test",
            baseline_environment="prod",
            parity_status="parity-preserving-difference",
            differences=["synthetic_inputs_only"],
            owner="qa",
        ),
        EnvironmentParityRecord(
            environment="staging",
            baseline_environment="prod",
            parity_status="parity-preserving-difference",
            differences=["canary_gate_enabled"],
            owner="operator",
        ),
        EnvironmentParityRecord(
            environment="local",
            baseline_environment="prod",
            parity_status="drift-risk",
            differences=["manual_overrides_possible", "ad_hoc_modules"],
            owner="developer",
        ),
        EnvironmentParityRecord(
            environment="drill",
            baseline_environment="prod",
            parity_status="known-divergence",
            differences=["fault_injection_enabled"],
            owner="resilience",
        ),
    ]



def classify_parity_status() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for x in build_environment_parity_records():
        out.setdefault(x.parity_status, []).append(x.environment)
    return {k: sorted(v) for k, v in out.items()}
