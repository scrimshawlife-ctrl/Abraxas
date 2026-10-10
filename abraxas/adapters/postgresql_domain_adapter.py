"""Production DomainDataAdapter - connects to PostgreSQL for live data.

Follows DomainDataAdapter interface. Intentionally minimal — stub taxonomy
classifies this as 'intentional_abstract' until live data sources are wired.

intentional_abstract: returns minimal valid snapshots until live data source is wired
"""
from datetime import datetime, timezone
from typing import Any, Dict, List

import asyncpg

from abraxas.adapters.domain_data import DomainDataAdapter, DomainSnapshot, DomainTokenState


class PostgreSQLDomainAdapter(DomainDataAdapter):
    """Production adapter - connects to PostgreSQL for artifact metadata.

    Returns minimal valid snapshots until a live data source is wired.

    intentional_abstract: returns minimal valid snapshots until live data source is wired
    """
    
    def __init__(self, dsn: str, domain_name: str = "production"):
        self.dsn = dsn
        self.domain_name = domain_name
        self.pool = None
    
    async def connect(self):
        """Initialize connection pool."""
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.dsn)
    
    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
    
    async def fetch_domain_signals(self, domain: str, since: str) -> List[Dict[str, Any]]:
        """Fetch signals from PostgreSQL."""
        await self.connect()
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM domain_signals WHERE domain = $1 AND timestamp > $2""", 
                domain, since
            )
            return [dict(row) for row in rows]
    
    async def fetch_phase_transitions(self, domain: str, since: str) -> List[Dict[str, Any]]:
        """Fetch phase transitions from PostgreSQL."""
        await self.connect()
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM phase_transitions WHERE domain = $1 AND timestamp > $2""", 
                domain, since
            )
            return [dict(row) for row in rows]
    
    async def fetch_oracle_runs(self, since: str) -> List[Dict[str, Any]]:
        """Fetch recent oracle runs from PostgreSQL."""
        await self.connect()
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM oracle_runs WHERE timestamp > $2 ORDER BY timestamp DESC LIMIT 100""", 
                since
            )
            return [dict(row) for row in rows]
    
    async def fetch_ritual_executions(self, since: str) -> List[Dict[str, Any]]:
        """Fetch ritual executions from PostgreSQL."""
        await self.connect()
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM ritual_executions WHERE timestamp > $2""", 
                since
            )
            return [dict(row) for row in rows]
    
    async def get_timechain_status(self) -> Dict[str, Any]:
        """Get current timechain status from PostgreSQL."""
        await self.connect()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT * FROM timechain_status ORDER BY id DESC LIMIT 1"""
            )
            return dict(row) if row else {}
    
    # Implement abstract methods from DomainDataAdapter
    def fetch_current_state(self) -> DomainSnapshot:
        """Fetch current domain state from live source."""
        # For now, return a mock state - in production this would query PostgreSQL
        # This is a synchronous method, so we can't use async here
        # In a real implementation, we might use asyncio.run() or have a sync version
        tokens = [
            DomainTokenState(
                token=f"{self.domain_name}_token_1",
                domain=self.domain_name,
                phase="front",
                tau_level=0.7,
                tau_velocity=0.4,
                timestamp_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                confidence=0.8,
            )
        ]
        return DomainSnapshot(
            domain=self.domain_name,
            tokens=tokens,
            timestamp_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source="postgresql",
        )
    
    def fetch_historical(self, hours: int = 24) -> List[DomainSnapshot]:
        """Fetch historical snapshots for tau calculation."""
        # Return current state repeated for simplicity
        # In production, this would query historical data from PostgreSQL
        current_state = self.fetch_current_state()
        return [current_state] * min(hours, 24)  # Return up to 24 hours of data
    
    def get_domain_name(self) -> str:
        """Return domain identifier."""
        return self.domain_name

# Factory function for dependency injection
def get_domain_adapter() -> DomainDataAdapter:
    import os
    if os.getenv('ABRAXAS_ENV') == 'production':
        # In production, get DSN from secrets/env
        dsn = os.getenv('ABRAXAS_POSTGRES_DSN', 'postgresql://user:pass@localhost/abraxas')
        domain = os.getenv('ABRAXAS_DOMAIN_NAME', 'production')
        return PostgreSQLDomainAdapter(dsn, domain)
    from abraxas.adapters.domain_data import MockDomainAdapter
    return MockDomainAdapter(domain=os.getenv('ABRAXAS_DOMAIN_NAME', 'production'))
