"""Overlay Schema

Defines schemas and validation for overlay operations.
"""

from typing import Any, Dict, Optional, Literal
from dataclasses import dataclass, field

# Phase type definition
Phase = Literal["OPEN", "ALIGN", "CLEAR", "SEAL", "ASCEND"]


@dataclass
class OverlaySchema:
    """Schema definition for overlay operations."""

    name: str
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate data against the schema.

        Args:
            data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        for field_name, field_spec in self.fields.items():
            if field_spec.get("required", False) and field_name not in data:
                return False

            if field_name in data:
                expected_type = field_spec.get("type")
                if expected_type and not isinstance(data[field_name], expected_type):
                    return False

        return True

    def add_field(self, name: str, field_type: type, required: bool = False, **kwargs):
        """Add a field to the schema.

        Args:
            name: Field name
            field_type: Expected type for the field
            required: Whether the field is required
            **kwargs: Additional field specifications
        """
        self.fields[name] = {
            "type": field_type,
            "required": required,
            **kwargs
        }
