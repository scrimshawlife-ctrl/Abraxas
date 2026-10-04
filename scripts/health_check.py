#!/usr/bin/env python3
"""
Health check script for Abraxas.
Used by Kubernetes liveness and readiness probes.
"""
import sys
import traceback

def main():
    try:
        # Import Abraxas components
        from abraxas.governance.production import ProductionOrchestrator
        from abraxas.yggdrasil.memory import CypherMemoryLayer
        
        # Initialize orchestrator
        orchestrator = ProductionOrchestrator()
        orchestrator.initialize()
        
        # Initialize memory layer
        memory = CypherMemoryLayer()
        memory.initialize()
        
        # Get system status to verify basic functionality
        status = orchestrator.get_system_status()
        
        # Check that orchestrator is initialized
        if not status.get('initialized', False):
            raise Exception("Orchestrator not initialized")
        
        # Optionally, we can also check memory layer status
        mem_status = memory.get_status()
        if not mem_status.get('initialized', False):
            raise Exception("Memory layer not initialized")
        
        # If we get here, the system is healthy
        print("Health check passed")
        sys.exit(0)
        
    except Exception as e:
        print(f"Health check failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()