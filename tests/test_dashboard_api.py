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
    from abraxas.dashboard.api import app, domain_adapter
    print("✓ Successfully imported dashboard API")
    print(f"✓ Domain adapter type: {type(domain_adapter).__name__}")
    print(f"✓ Domain adapter domain: {domain_adapter.get_domain_name()}")
    
    # Test that we can access the FastAPI app
    print(f"✓ FastAPI app title: {app.title}")
    print(f"✓ FastAPI app version: {app.version}")
    
    print("\n🎉 Dashboard API import successful!")
    
except Exception as e:
    print(f"✗ Error importing dashboard API: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)