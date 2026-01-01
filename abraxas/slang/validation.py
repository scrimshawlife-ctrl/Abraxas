"""Lifecycle State Validation Utilities

Validates lifecycle states across the system to ensure consistency.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from abraxas.slang.lifecycle import LifecycleState


class LifecycleStateValidator:
    """Validates lifecycle state data for consistency."""

    VALID_STATES = {"Proto", "Front", "Saturated", "Dormant", "Archived"}

    @staticmethod
    def is_valid_state(state: str) -> bool:
        """Check if a state string is valid.

        Args:
            state: Lifecycle state string to validate

        Returns:
            True if state is valid canonical format
        """
        return state in LifecycleStateValidator.VALID_STATES

    @staticmethod
    def validate_state(state: str) -> LifecycleState:
        """Validate and convert state string to LifecycleState enum.

        Args:
            state: Lifecycle state string

        Returns:
            LifecycleState enum value

        Raises:
            ValueError: If state is invalid
        """
        if not LifecycleStateValidator.is_valid_state(state):
            raise ValueError(
                f"Invalid lifecycle state: '{state}'. "
                f"Must be one of: {', '.join(LifecycleStateValidator.VALID_STATES)}"
            )
        return LifecycleState(state)

    @staticmethod
    def validate_state_dict(
        state_dict: Dict[str, str],
        raise_on_error: bool = True,
    ) -> Tuple[bool, List[str]]:
        """Validate a dictionary of token → lifecycle_state mappings.

        Args:
            state_dict: Dictionary mapping tokens to lifecycle states
            raise_on_error: If True, raise ValueError on first invalid state

        Returns:
            Tuple of (all_valid, list_of_errors)

        Raises:
            ValueError: If raise_on_error=True and invalid state found
        """
        errors = []

        for token, state in state_dict.items():
            if not LifecycleStateValidator.is_valid_state(state):
                error_msg = f"Token '{token}' has invalid state '{state}'"
                errors.append(error_msg)

                if raise_on_error:
                    raise ValueError(error_msg)

        return (len(errors) == 0, errors)

    @staticmethod
    def normalize_state(state: str) -> str:
        """Normalize a lifecycle state to canonical format.

        Handles common variations:
        - "proto" → "Proto"
        - "FRONT" → "Front"
        - "saturated" → "Saturated"

        Args:
            state: Lifecycle state string (any case)

        Returns:
            Canonical PascalCase state string

        Raises:
            ValueError: If state cannot be normalized
        """
        # Map lowercase to canonical
        state_map = {
            "proto": "Proto",
            "front": "Front",
            "saturated": "Saturated",
            "dormant": "Dormant",
            "archived": "Archived",
        }

        # Try exact match first
        if state in LifecycleStateValidator.VALID_STATES:
            return state

        # Try lowercase normalization
        normalized = state_map.get(state.lower())
        if normalized:
            return normalized

        raise ValueError(
            f"Cannot normalize lifecycle state: '{state}'. "
            f"Expected one of: {', '.join(LifecycleStateValidator.VALID_STATES)}"
        )

    @staticmethod
    def migrate_state_dict(state_dict: Dict[str, str]) -> Dict[str, str]:
        """Migrate a state dictionary from old format to canonical.

        Useful for migrating stored data from lowercase to PascalCase.

        Args:
            state_dict: Dictionary with potentially old-format states

        Returns:
            Dictionary with canonical PascalCase states
        """
        migrated = {}
        for token, state in state_dict.items():
            try:
                migrated[token] = LifecycleStateValidator.normalize_state(state)
            except ValueError:
                # Keep original if normalization fails
                migrated[token] = state

        return migrated


def validate_lifecycle_state(state: str) -> bool:
    """Quick validation check for lifecycle state.

    Args:
        state: Lifecycle state string to validate

    Returns:
        True if valid, False otherwise
    """
    return LifecycleStateValidator.is_valid_state(state)


def normalize_lifecycle_state(state: str) -> str:
    """Quick normalization of lifecycle state.

    Args:
        state: Lifecycle state string (any case)

    Returns:
        Canonical PascalCase state string

    Raises:
        ValueError: If state cannot be normalized
    """
    return LifecycleStateValidator.normalize_state(state)
