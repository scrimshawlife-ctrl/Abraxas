"""Domain Data Adapter Interface for Live Streams

Implement this interface for each domain data source.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class DomainTokenState:
    """Single token's lifecycle state."""
    token: str
    domain: str
    phase: str  # proto/front/saturated/dormant/archived
    tau_level: float
    tau_velocity: float
    timestamp_utc: str
    confidence: float


@dataclass
class DomainSnapshot:
    """Complete domain state snapshot."""
    domain: str
    tokens: List[DomainTokenState]
    timestamp_utc: str
    source: str


class DomainDataAdapter(ABC):
    """Abstract adapter for domain data streams."""
    
    @abstractmethod
    def fetch_current_state(self) -> DomainSnapshot:
        """Fetch current domain state from live source."""
        pass
    
    @abstractmethod
    def fetch_historical(self, hours: int = 24) -> List[DomainSnapshot]:
        """Fetch historical snapshots for tau calculation."""
        pass
    
    @abstractmethod
    def get_domain_name(self) -> str:
        """Return domain identifier."""
        pass


class MockDomainAdapter(DomainDataAdapter):
    """Mock adapter for testing."""
    
    def __init__(self, domain: str):
        self._domain = domain
    
    def fetch_current_state(self) -> DomainSnapshot:
        # Return mock data matching test fixtures
        tokens = [
            DomainTokenState(
                token=f"{self._domain}_token_1",
                domain=self._domain,
                phase="front",
                tau_level=0.7,
                tau_velocity=0.4,
                timestamp_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                confidence=0.8,
            )
        ]
        return DomainSnapshot(
            domain=self._domain,
            tokens=tokens,
            timestamp_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source="mock",
        )
    
    def fetch_historical(self, hours: int = 24) -> List[DomainSnapshot]:
        return [self.fetch_current_state()]
    
    def get_domain_name(self) -> str:
        return self._domain