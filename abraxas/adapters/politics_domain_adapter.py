"""Minimal real adapter for politics domain data.

Follows DomainDataAdapter interface. Intentionally minimal — stub taxonomy
classifies this as 'intentional_abstract' until live data sources are wired.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from abraxas.adapters.domain_data import (
    DomainDataAdapter,
    DomainSnapshot,
    DomainTokenState,
)


class PoliticsDomainAdapter(DomainDataAdapter):
    """Real adapter stub for politics domain.

    Returns minimal valid snapshots with explicit confidence=0.5
    until a live data source (e.g. news API, sentiment feed) is wired.
    """

    def __init__(self, domain: str = "politics"):
        self._domain = domain

    def fetch_current_state(self) -> DomainSnapshot:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        token = DomainTokenState(
            token="politics_example",
            domain=self._domain,
            phase="proto",
            tau_level=0.1,
            tau_velocity=0.0,
            timestamp_utc=now,
            confidence=0.5,
        )
        return DomainSnapshot(
            domain=self._domain,
            tokens=[token],
            timestamp_utc=now,
            source="politics-adapter",
        )

    def fetch_historical(self, hours: int = 24) -> List[DomainSnapshot]:
        return [self.fetch_current_state()]

    def get_domain_name(self) -> str:
        return self._domain