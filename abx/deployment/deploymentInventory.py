from __future__ import annotations

from abx.deployment.types import DeploymentContractRecord



def build_deployment_contract_inventory() -> list[DeploymentContractRecord]:
    return [
        DeploymentContractRecord(
            deployment_id="deploy.local.cli",
            entrypoint="python -m abx.apply_cli",
            environment="local",
            classification="authoritative",
            owner="runtime",
            expected_inputs=["config.profile", "run_id"],
            expected_topology="topology.single-process",
            postconditions=["runtime.booted", "trace.enabled"],
        ),
        DeploymentContractRecord(
            deployment_id="deploy.ci.validation",
            entrypoint="python -m pytest",
            environment="test",
            classification="derived",
            owner="governance",
            expected_inputs=["config.profile", "test.selection"],
            expected_topology="topology.validation-runner",
            postconditions=["contracts.validated", "scorecards.stable"],
        ),
        DeploymentContractRecord(
            deployment_id="deploy.prod.orchestrated",
            entrypoint="python -m abx.runtime_orchestrator",
            environment="production-like",
            classification="authoritative",
            owner="operator",
            expected_inputs=["config.profile", "secret.bundle", "topology.manifest"],
            expected_topology="topology.distributed-core",
            postconditions=["runtime.steady", "observability.bound"],
        ),
        DeploymentContractRecord(
            deployment_id="deploy.legacy.shell",
            entrypoint="./legacy_start.sh",
            environment="dev",
            classification="legacy",
            owner="operator",
            expected_inputs=["env.vars"],
            expected_topology="topology.single-process",
            postconditions=["runtime.booted"],
        ),
    ]
