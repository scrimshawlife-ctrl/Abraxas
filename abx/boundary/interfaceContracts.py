from __future__ import annotations

from abx.boundary.types import InterfaceContractRecord


def build_interface_contracts() -> list[InterfaceContractRecord]:
    contracts = [
        InterfaceContractRecord(
            interface_id="runtime_orchestrator.execute_run_plan",
            version="v1",
            owner="runtime",
            required_fields=["run_id", "scenario_id"],
            optional_fields=["previous_run_id", "continuity_mode"],
            exposure="INTERNAL",
        ),
        InterfaceContractRecord(
            interface_id="operator_workflows.run_operator_workflow",
            version="v1",
            owner="operations",
            required_fields=["workflow", "payload"],
            optional_fields=[],
            exposure="SEMI_PUBLIC",
        ),
        InterfaceContractRecord(
            interface_id="scripts.run_boundary_validation",
            version="v1",
            owner="governance",
            required_fields=["source", "interface_id", "payload"],
            optional_fields=["received_tick", "current_tick"],
            exposure="PUBLIC_CLI",
        ),
    ]
    return sorted(contracts, key=lambda x: x.interface_id)
