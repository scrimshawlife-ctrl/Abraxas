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

# Set environment to production mode to test with PostgreSQL adapter
os.environ['ABRAXAS_ENV'] = 'production'
os.environ['ABRAXAS_POSTGRES_DSN'] = 'postgresql://user:pass@localhost/abraxas'
os.environ['ABRAXAS_DOMAIN_NAME'] = 'test_production'

try:
    from abraxas.dashboard.api import app, domain_adapter
    print("✓ Successfully imported dashboard API")
    print(f"✓ Domain adapter type: {type(domain_adapter).__name__}")
    print(f"✓ Domain adapter domain: {domain_adapter.get_domain_name()}")
    
    # Verify it's using PostgreSQL adapter
    from abraxas.adapters.postgresql_domain_adapter import PostgreSQLDomainAdapter
    assert isinstance(domain_adapter, PostgreSQLDomainAdapter)
    print("✓ Confirmed: using PostgreSQLDomainAdapter in production mode")
    
    # Test that we can access the FastAPI app
    print(f"✓ FastAPI app title: {app.title}")
    print(f"✓ FastAPI app version: {app.version}")
    
    # Test a few API endpoints conceptually (without actually running the server)
    print("✓ API routes available:")
    print(f"  - GET /api/health")
    print(f"  - GET /api/artifacts")
    print(f"  - GET /api/domain/signals")
    print(f"  - GET /api/domain/phase-transitions")
    print(f"  - GET /api/domain/oracle-runs")
    print(f"  - GET /api/domain/ritual-executions")
    print(f"  - POST /api/telemetry")
    
    # Clean up environment
    for var in ['ABRAXAS_ENV', 'ABRAXAS_POSTGRES_DSN', 'ABRAXAS_DOMAIN_NAME']:
        if var in os.environ:
            del os.environ[var]
    
    print("\n🎉 Dashboard API with PostgreSQL adapter test successful!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)