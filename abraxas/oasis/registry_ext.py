"""Registry extensions for OAS operators."""

from __future__ import annotations

from abraxas.core.registry import OperatorRegistry
from abraxas.oasis.models import OperatorCandidate, OperatorStatus


class OASRegistryExtension:
    """
    Extension methods for OperatorRegistry specific to OAS.

    Provides higher-level operations for OAS workflow.
    """

    def __init__(self, registry: OperatorRegistry):
        """
        Initialize with a registry instance.

        Args:
            registry: OperatorRegistry to extend
        """
        self.registry = registry

    def register_candidate(self, candidate: OperatorCandidate) -> None:
        """
        Register an operator candidate.

        Args:
            candidate: Candidate to register
        """
        self.registry.register(
            operator_id=candidate.operator_id,
            version=candidate.version,
            status=candidate.status.value,
            data=candidate.model_dump(),
        )

    def promote_to_canonical(self, operator_id: str) -> bool:
        """
        Promote an operator from staging to canonical.

        Args:
            operator_id: Operator to promote

        Returns:
            True if successful, False if operator not found
        """
        entry = self.registry.get(operator_id)
        if not entry:
            return False

        # Update status to canonical
        data = entry.data.copy()
        data["status"] = OperatorStatus.CANONICAL.value

        self.registry.register(
            operator_id=operator_id,
            version=entry.version,
            status=OperatorStatus.CANONICAL.value,
            data=data,
        )

        return True

    def demote_to_legacy(self, operator_id: str) -> bool:
        """
        Demote an operator to legacy status.

        Args:
            operator_id: Operator to demote

        Returns:
            True if successful, False if operator not found
        """
        entry = self.registry.get(operator_id)
        if not entry:
            return False

        data = entry.data.copy()
        data["status"] = OperatorStatus.LEGACY.value

        self.registry.register(
            operator_id=operator_id,
            version=entry.version,
            status=OperatorStatus.LEGACY.value,
            data=data,
        )

        return True

    def deprecate(self, operator_id: str) -> bool:
        """
        Mark an operator as deprecated.

        Args:
            operator_id: Operator to deprecate

        Returns:
            True if successful, False if operator not found
        """
        entry = self.registry.get(operator_id)
        if not entry:
            return False

        data = entry.data.copy()
        data["status"] = OperatorStatus.DEPRECATED.value

        self.registry.register(
            operator_id=operator_id,
            version=entry.version,
            status=OperatorStatus.DEPRECATED.value,
            data=data,
        )

        return True

    def list_by_status(self, status: OperatorStatus) -> list[dict]:
        """
        List all operators with given status.

        Args:
            status: Status to filter by

        Returns:
            List of operator data dicts
        """
        entries = self.registry.registry.list_by_status(status.value)
        return [entry.data for entry in entries]

    def get_operator_data(self, operator_id: str) -> dict | None:
        """
        Get full operator data.

        Args:
            operator_id: Operator ID

        Returns:
            Operator data dict or None
        """
        entry = self.registry.get(operator_id)
        return entry.data if entry else None
