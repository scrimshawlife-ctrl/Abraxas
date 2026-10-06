#!/usr/bin/env python3
import sys
import os

# Add the project root to the path
sys.path.insert(0, '/Users/appliedalchemylabs/Abraxas')

# Clear any cached modules
modules_to_remove = [k for k in sys.modules.keys() if 'abraxas' in k]
for mod in modules_to_remove:
    if mod in sys.modules:
        del sys.modules[mod]

try:
    from abraxas.adapters.postgresql_domain_adapter import PostgreSQLDomainAdapter, get_domain_adapter
    print("✓ Successfully imported PostgreSQLDomainAdapter and get_domain_adapter")
    
    # Test instantiation
    adapter = PostgreSQLDomainAdapter("postgresql://test:test@localhost/test", "test_domain")
    print("✓ Successfully instantiated PostgreSQLDomainAdapter")
    
    # Test abstract methods
    state = adapter.fetch_current_state()
    print(f"✓ fetch_current_state works: domain={state.domain}, tokens={len(state.tokens)}")
    
    history = adapter.fetch_historical(2)
    print(f"✓ fetch_historical works: {len(history)} snapshots")
    
    domain_name = adapter.get_domain_name()
    print(f"✓ get_domain_name works: {domain_name}")
    
    # Test factory function in development mode
    # Clear relevant environment variables
    if 'ABRAXAS_ENV' in os.environ:
        del os.environ['ABRAXAS_ENV']
    if 'ABRAXAS_DOMAIN_NAME' in os.environ:
        del os.environ['ABRAXAS_DOMAIN_NAME']
    
    dev_adapter = get_domain_adapter()
    from abraxas.adapters.domain_data import MockDomainAdapter
    print(f"✓ Dev factory returned: {type(dev_adapter).__name__}")
    assert isinstance(dev_adapter, MockDomainAdapter)
    
    # Test factory function in production mode
    os.environ['ABRAXAS_ENV'] = 'production'
    os.environ['ABRAXAS_POSTGRES_DSN'] = 'postgresql://user:pass@localhost/abraxas'
    os.environ['ABRAXAS_DOMAIN_NAME'] = 'test_production'
    
    prod_adapter = get_domain_adapter()
    print(f"✓ Prod factory returned: {type(prod_adapter).__name__}")
    assert isinstance(prod_adapter, PostgreSQLDomainAdapter)
    assert prod_adapter.dsn == 'postgresql://user:pass@localhost/abraxas'
    assert prod_adapter.domain_name == 'test_production'
    
    # Test that the production adapter works
    prod_state = prod_adapter.fetch_current_state()
    print(f"✓ Prod adapter state: domain={prod_state.domain}")
    
    # Clean up environment
    for var in ['ABRAXAS_ENV', 'ABRAXAS_POSTGRES_DSN', 'ABRAXAS_DOMAIN_NAME']:
        if var in os.environ:
            del os.environ[var]
    
    print("\n🎉 All tests passed! PostgreSQLDomainAdapter is working correctly.")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)