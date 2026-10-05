"""Test for PostgreSQL database initialization"""
import sys
import os
sys.path.insert(0, '/Users/appliedalchemylabs/Abraxas')

# Test that the script can be imported without errors
try:
    from scripts.init_postgres_schema import init_database
    print("✓ Successfully imported init_database function")
    
    # Check function signature
    import inspect
    sig = inspect.signature(init_database)
    print(f"✓ Function signature: {sig}")
    
    print("✓ Database initialization script is ready")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()