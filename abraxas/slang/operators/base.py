"""Base operator protocol and classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from abraxas.core.resonance_frame import ResonanceFrame
from abraxas.slang.models import OperatorReadout


class OperatorStatus(str, Enum):
    """Status of an operator in the registry."""

    STAGING = "staging"
    CANONICAL = "canonical"
    LEGACY = "legacy"
    DEPRECATED = "deprecated"


class Operator(ABC, BaseModel):
    """
    Base class for all slang operators.

    Operators analyze text/frames and produce readouts (classifications, features, etc.).
    """

    operator_id: str = Field(..., description="Unique operator identifier")
    version: str = Field(default="1.0.0", description="Operator version")
    status: OperatorStatus = Field(default=OperatorStatus.STAGING, description="Operator status")
    scope: dict[str, Any] = Field(
        default_factory=dict, description="Scope metadata (languages, domains, etc.)"
    )
    failure_modes: list[str] = Field(
        default_factory=list, description="Known failure modes or edge cases"
    )

    class Config:
        # Allow subclassing with pydantic
        arbitrary_types_allowed = True

    @abstractmethod
    def apply(self, text: str, frame: ResonanceFrame | None = None) -> OperatorReadout | None:
        """
        Apply operator to text/frame.

        Args:
            text: Text to analyze
            frame: Optional full resonance frame for additional context

        Returns:
            OperatorReadout if operator fires, None otherwise
        """
        pass

    def __hash__(self) -> int:
        """Hash based on operator_id and version."""
        return hash((self.operator_id, self.version))
