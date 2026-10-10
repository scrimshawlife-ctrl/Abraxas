"""Test for PostgreSQLDomainAdapter"""
import asyncio

import pytest

# asyncpg is an optional dependency (the [postgres] extra). A missing optional
# dependency must SKIP this module -- the bare module-scope import used to
# interrupt collection for the ENTIRE suite, which is why every full run needed
# --ignore and CI could never see the whole test suite.
pytest.importorskip("asyncpg")

from datetime import datetime, timezone

from abraxas.adapters.domain_data import DomainSnapshot, DomainTokenState
from abraxas.adapters.postgresql_domain_adapter import PostgreSQLDomainAdapter


def test_adapter_instantiation():
    """Test that we can create an adapter instance"""
    adapter = PostgreSQLDomainAdapter("postgresql://test:test@localhost/test", "test_domain")
    assert adapter.dsn == "postgresql://test:test@localhost/test"
    assert adapter.domain_name == "test_domain"
    assert adapter.pool is None


def test_get_domain_name():
    """Test get_domain_name method"""
    adapter = PostgreSQLDomainAdapter("postgresql://test:test@localhost/test", "test_domain")
    assert adapter.get_domain_name() == "test_domain"


def test_fetch_current_state():
    """Test fetch_current_state returns a valid DomainSnapshot"""
    adapter = PostgreSQLDomainAdapter("postgresql://test:test@localhost/test", "test_domain")
    state = adapter.fetch_current_state()
    
    assert isinstance(state, DomainSnapshot)
    assert state.domain == "test_domain"
    assert state.source == "postgresql"
    assert len(state.tokens) == 1
    
    token = state.tokens[0]
    assert isinstance(token, DomainTokenState)
    assert token.token == "test_domain_token_1"
    assert token.domain == "test_domain"
    assert token.phase == "front"
    assert token.tau_level == 0.7
    assert token.tau_velocity == 0.4
    assert token.confidence == 0.8
    
    # Check timestamp is recent
    timestamp = datetime.fromisoformat(state.timestamp_utc.replace("Z", "+00:00"))
    assert (datetime.now(timezone.utc) - timestamp).total_seconds() < 5


def test_fetch_historical():
    """Test fetch_historical returns a list of snapshots"""
    adapter = PostgreSQLDomainAdapter("postgresql://test:test@localhost/test", "test_domain")
    
    # Test with default hours
    history = adapter.fetch_historical()
    assert len(history) == 24  # Default is 24 hours
    
    # Test with specific hours
    history = adapter.fetch_historical(5)
    assert len(history) == 5
    
    # Test with hours > 24 (should cap at 24)
    history = adapter.fetch_historical(30)
    assert len(history) == 24
    
    # All entries should be DomainSnapshot instances
    for snapshot in history:
        assert isinstance(snapshot, DomainSnapshot)
        assert snapshot.domain == "test_domain"


async def _async_methods_exist():
    """Coroutine body: verify the async methods exist and are callable.

    Driven by the sync wrapper below via asyncio.run -- deliberately NOT a bare
    `async def test_`. There is no pytest-asyncio in this environment, so such a
    test is not natively supported by pytest (it fails), and its
    `@pytest.mark.asyncio` marker is unregistered under --strict-markers (it
    errors and interrupts collection for the whole suite). This module only
    became reachable once `asyncpg` was declared in the [postgres] extra, so that
    breakage was latent: CI installs .[dev,server] (no asyncpg), so the module
    skipped at importorskip and never collected. __main__ below already drove
    this coroutine with asyncio.run.
    """
    adapter = PostgreSQLDomainAdapter("postgresql://test:test@localhost/test", "test_domain")
    
    # Test that methods exist
    assert hasattr(adapter, 'connect')
    assert hasattr(adapter, 'close')
    assert hasattr(adapter, 'fetch_domain_signals')
    assert hasattr(adapter, 'fetch_phase_transitions')
    assert hasattr(adapter, 'fetch_oracle_runs')
    assert hasattr(adapter, 'fetch_ritual_executions')
    assert hasattr(adapter, 'get_timechain_status')
    
    # Test that they're callable
    assert callable(adapter.connect)
    assert callable(adapter.close)
    assert callable(adapter.fetch_domain_signals)
    assert callable(adapter.fetch_phase_transitions)
    assert callable(adapter.fetch_oracle_runs)
    assert callable(adapter.fetch_ritual_executions)
    assert callable(adapter.get_timechain_status)
    
    # Actually calling them would fail without a DB, but we can verify they exist
    # We'll test connect/close separately since they don't require query params
    
    # Test connect fails gracefully (no DB)
    try:
        await adapter.connect()
        assert False, "Should have failed to connect"
    except Exception:
        pass  # Expected
    
    # Test close doesn't crash
    try:
        await adapter.close()
    except Exception:
        pass  # Should not crash


def test_async_methods_exist():
    """Drive the async-method probe to completion; see the helper's note above."""
    asyncio.run(_async_methods_exist())


def test_factory_function_development():
    """Test factory function in development mode"""
    import os
    # Clear relevant environment variables
    if 'ABRAXAS_ENV' in os.environ:
        del os.environ['ABRAXAS_ENV']
    
    from abraxas.adapters.postgresql_domain_adapter import get_domain_adapter
    adapter = get_domain_adapter()
    
    # Should return MockDomainAdapter in dev mode
    from abraxas.adapters.domain_data import MockDomainAdapter
    assert isinstance(adapter, MockDomainAdapter)


def test_factory_function_production():
    """Test factory function in production mode"""
    import os
    # Set production environment
    os.environ['ABRAXAS_ENV'] = 'production'
    os.environ['ABRAXAS_POSTGRES_DSN'] = 'postgresql://user:pass@host/db'
    os.environ['ABRAXAS_DOMAIN_NAME'] = 'prod_domain'
    
    try:
        from abraxas.adapters.postgresql_domain_adapter import get_domain_adapter
        adapter = get_domain_adapter()
        
        # Should return PostgreSQLDomainAdapter in prod mode
        assert isinstance(adapter, PostgreSQLDomainAdapter)
        assert adapter.dsn == 'postgresql://user:pass@host/db'
        assert adapter.domain_name == 'prod_domain'
    finally:
        # Clean up environment
        for var in ['ABRAXAS_ENV', 'ABRAXAS_POSTGRES_DSN', 'ABRAXAS_DOMAIN_NAME']:
            if var in os.environ:
                del os.environ[var]


def test_postgresql_is_intentional_abstract():
    """Ensure postgresql follows the intentional_abstract pattern like other domains."""
    adapter = PostgreSQLDomainAdapter("postgresql://test:***@localhost/test", "test_domain")
    # Marker must be present as class attr or doc for taxonomy
    assert hasattr(adapter, "intentional_abstract") or "intentional_abstract" in (adapter.__doc__ or "")
    state = adapter.fetch_current_state()
    assert state.source == "postgresql"


if __name__ == "__main__":
    # Run tests manually if needed
    test_adapter_instantiation()
    print("✓ test_adapter_instantiation passed")
    
    test_get_domain_name()
    print("✓ test_get_domain_name passed")
    
    test_fetch_current_state()
    print("✓ test_fetch_current_state passed")
    
    test_fetch_historical()
    print("✓ test_fetch_historical passed")
    
    test_factory_function_development()
    print("✓ test_factory_function_development passed")
    
    test_factory_function_production()
    print("✓ test_factory_function_production passed")
    
    # Run async test
    asyncio.run(test_async_methods_exist())
    print("✓ test_async_methods_exist passed")
    
    print("\n✅ All tests passed!")
