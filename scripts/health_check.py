#!/usr/bin/env python3
"""
Health check script for Abraxas.
Used by Kubernetes liveness and readiness probes.
Supports three modes:
- --check-live: Liveness probe (process alive)
- --check-ready: Readiness probe (orchestrator initialized, memory layer healthy)
- --check-metrics: Metrics endpoint (Prometheus format)
- --check-all: Run all checks
"""
import sys
import traceback
import argparse

def check_live():
    """Liveness probe - process is alive."""
    print("✓ Liveness: OK")
    return True

def check_ready():
    """Readiness probe - orchestrator and memory layer initialized."""
    try:
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
        
        print("✓ Readiness: OK (orchestrator initialized, memory layer healthy)")
        return True
    except Exception as e:
        print(f"✗ Readiness: FAILED - {e}")
        return False

def check_metrics():
    """Metrics endpoint - Prometheus format."""
    try:
        from abraxas.governance.production import ProductionOrchestrator
        
        orchestrator = ProductionOrchestrator()
        orchestrator.initialize()
        
        # Get system status
        status = orchestrator.get_system_status()
        
        # Output in Prometheus format
        print(f"abraxas_engine_registry_initialized {1 if status.get('engine_registry_initialized') else 0}")
        print(f"abraxas_engine_count {status.get('engine_count', 0)}")
        print(f"abraxas_total_audit_entries {status.get('total_audit_entries', 0)}")
        
        policy = status.get('policy_config', {})
        print(f"abraxas_policy_accept_confidence {policy.get('accept_confidence', 0)}")
        print(f"abraxas_policy_verify_confidence {policy.get('verify_confidence', 0)}")
        print(f"abraxas_policy_recompute_confidence {policy.get('recompute_confidence', 0)}")
        print(f"abraxas_policy_max_uncertainty {policy.get('max_uncertainty', 0)}")
        print(f"abraxas_policy_min_decision_margin {policy.get('min_decision_margin', 0)}")
        print(f"abraxas_policy_max_entropy {policy.get('max_entropy', 0)}")
        
        print("✓ Metrics: OK (Prometheus format)")
        return True
    except Exception as e:
        print(f"✗ Metrics: FAILED - {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Abraxas health check")
    parser.add_argument("--check-live", action="store_true", help="Liveness probe")
    parser.add_argument("--check-ready", action="store_true", help="Readiness probe")
    parser.add_argument("--check-metrics", action="store_true", help="Metrics endpoint")
    parser.add_argument("--check-all", action="store_true", help="Run all checks")
    args = parser.parse_args()
    
    if not any([args.check_live, args.check_ready, args.check_metrics, args.check_all]):
        parser.print_help()
        sys.exit(1)
    
    results = []
    
    if args.check_live or args.check_all:
        results.append(check_live())
    
    if args.check_ready or args.check_all:
        results.append(check_ready())
    
    if args.check_metrics or args.check_all:
        results.append(check_metrics())
    
    if all(results):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()