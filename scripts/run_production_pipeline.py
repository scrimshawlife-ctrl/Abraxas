#!/usr/bin/env python3
"""Production Pipeline Runner

Runs the integrated Abraxas pipeline against live domain data.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from typing import Dict, List

from abraxas.adapters.domain_data import DomainDataAdapter, MockDomainAdapter
from abraxas.adapters.finance_domain_adapter import FinanceDomainAdapter
from abraxas.adapters.media_domain_adapter import MediaDomainAdapter
from abraxas.adapters.politics_domain_adapter import PoliticsDomainAdapter
from abraxas.adapters.postgresql_domain_adapter import PostgreSQLDomainAdapter
from abraxas.core.temporal_tau import Observation, TauCalculator
from abraxas.oracle.v2.bundle import run_bundle
from abraxas.phase.detector import create_phase_detector
from abraxas.phase.early_warning import create_early_warning_system
from abraxas.renderers.resonance_narratives import render_narrative_bundle
from abraxas.ritual import create_ritual_engine


class ProductionPipeline:
    """Runs the full Abraxas pipeline in production mode."""
    
    def __init__(
        self,
        domain_adapters: Dict[str, DomainDataAdapter],
        output_dir: str = "./output",
        cycle_interval_seconds: int = 300,
    ):
        self.domain_adapters = domain_adapters
        self.output_dir = output_dir
        self.cycle_interval = cycle_interval_seconds
        
        # Initialize components
        self.phase_detector = create_phase_detector()
        self.warning_system = create_early_warning_system()
        self.tau_calculator = TauCalculator()
        self.ritual_engine = create_ritual_engine()
        
        # State
        self.cycle_count = 0
    
    def run_cycle(self) -> Dict:
        """Execute one pipeline cycle."""
        self.cycle_count += 1
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        print(f"\n=== Cycle {self.cycle_count} at {timestamp} ===")
        
        # 1. Fetch domain states
        domain_states = {}
        tau_snapshots = {}
        current_phases = {}
        
        for domain, adapter in self.domain_adapters.items():
            snapshot = adapter.fetch_current_state()
            
            # Build token -> phase mapping for phase detector
            token_phases = {t.token: t.phase for t in snapshot.tokens}
            domain_states[domain] = token_phases
            
            # Build tau snapshots
            observations = [
                Observation(ts=t.timestamp_utc, value=t.tau_level, source_id=t.token)
                for t in snapshot.tokens
            ]
            tau_snapshot = self.tau_calculator.compute_snapshot(
                observations, run_id=f"cycle-{self.cycle_count}"
            )
            tau_snapshots[domain] = tau_snapshot
            
            # Current phase (dominant)
            if token_phases:
                current_phases[domain] = max(set(token_phases.values()), key=list(token_phases.values()).count)
        
        # 2. Phase Detection
        alignments = self.phase_detector.detect_alignments(domain_states, timestamp_utc=timestamp)
        sync_map = self.phase_detector.build_synchronicity_map()

        # 2.5 Engine dispatch to planned stubs (more pipeline dispatch)
        engine_evidence = self._dispatch_to_engines(domain_states, alignments, timestamp)

        # 3. Early Warning
        warnings = self.warning_system.generate_warnings(
            tau_snapshots, current_phases, sync_map
        )
        
        # 4. Ritual Engine (check if any rituals should fire)
        ritual_executions = []
        for domain, phase in current_phases.items():
            # Check each protocol's preconditions against current state
            for protocol in self.ritual_engine.list_protocols():
                met, _ = self.ritual_engine.check_preconditions(protocol, {
                    "domain_phase": phase,
                    "tau_velocity": tau_snapshots[domain].tau_velocity,
                    "alignment_strength": 0.6,  # Would come from sync map
                    "domains_aligned": len([a for a in alignments if domain in a.domains]),
                    "cascade_risk": "MEDIUM",
                    "drift_resonance_detected": False,
                    "observation_count": tau_snapshots[domain].observation_count,
                    "confidence": tau_snapshots[domain].confidence.value,
                    "symbolic_state": "coherent",
                    "drift_detected": False,
                })
                if met:
                    # In production: add cooldown check
                    exec_result = self.ritual_engine.execute_ritual(
                        protocol.protocol_id,
                        operator="production_pipeline",
                        current_state={"domain_phase": phase, "tau_velocity": tau_snapshots[domain].tau_velocity},
                        timestamp_utc=timestamp,
                    )
                    ritual_executions.append(exec_result)
        
        # 5. Oracle Bundle (aggregate envelope)
        envelope = self._build_oracle_envelope(
            domain_states, alignments, warnings, ritual_executions, timestamp
        )
        
        # Run oracle bundle
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            bundle_result = run_bundle(
                envelope=envelope,
                config_hash="PRODUCTION_CONFIG_HASH",
                out_dir=td,
                do_stabilization_tick=True,
            )
        
        # 6. Resonance Narrative
        narrative = render_narrative_bundle(envelope)
        
        # 7. Output
        output = {
            "cycle": self.cycle_count,
            "timestamp": timestamp,
            "alignments": [a.to_dict() for a in alignments],
            "warnings": [w.to_dict() for w in warnings],
            "ritual_executions": [r.to_dict() for r in ritual_executions],
            "engine_evidence": [{"engine": getattr(e, 'engine', str(e)), "request_id": getattr(e, 'request_id', '')} for e in engine_evidence],
            "oracle_bundle": bundle_result,
            "narrative": narrative,
        }
        
        # Save to output dir
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = f"{self.output_dir}/cycle_{self.cycle_count:06d}.json"
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"  Alignments: {len(alignments)}")
        print(f"  Warnings: {len(warnings)}")
        print(f"  Rituals: {len(ritual_executions)}")
        print(f"  Oracle Bundle: {bundle_result['run_id']}")
        print(f"  Narrative: {narrative['artifact_id']}")
        print(f"  Saved: {output_path}")
        
        return output

    def _dispatch_to_engines(self, domain_states: Dict, alignments: List, timestamp: str) -> List:
        """Dispatch to planned stub engines for more pipeline integration.
        Uses manifest to resolve providers for resonance (phase), chronos (temporal), etc.
        Minimal dispatch for stubs.
        """
        envelopes = []
        from abraxas.engines.manifest import get
        from importlib import import_module

        # Resonance for phase alignments
        spec = get("resonance")
        if spec and spec.implementation:
            try:
                mod, attr = spec.implementation.split(":", 1)
                provider = getattr(import_module(mod), attr)()
                claim = f"resonance phase alignment dispatch for {len(alignments)} alignments at {timestamp}"
                env = provider.produce_evidence(f"dispatch-{self.cycle_count}", claim, {"alignments_count": len(alignments)})
                envelopes.append(env)
            except Exception:
                pass  # stub safe

        # Chronos for temporal
        spec = get("chronos")
        if spec and spec.implementation:
            try:
                mod, attr = spec.implementation.split(":", 1)
                provider = getattr(import_module(mod), attr)()
                claim = f"chronos temporal dispatch cycle {self.cycle_count}"
                env = provider.produce_evidence(f"dispatch-{self.cycle_count}", claim, {"cycle": self.cycle_count})
                envelopes.append(env)
            except Exception:
                pass

        # Aether (will raise but catch for stub)
        spec = get("aether")
        if spec and spec.implementation:
            try:
                mod, attr = spec.implementation.split(":", 1)
                provider = getattr(import_module(mod), attr)()
                env = provider.produce_evidence(f"dispatch-{self.cycle_count}", "aether multimodal", {})
                envelopes.append(env)
            except Exception:
                pass

        return envelopes

    def _build_oracle_envelope(
        self,
        domain_states: Dict,
        alignments: List,
        warnings: List,
        rituals: List,
        timestamp: str,
    ) -> Dict:
        """Build oracle signal envelope from pipeline state."""
        # Aggregate vital signals across domains
        vital_signals = []
        risk_signals = []
        patterns = []
        
        for domain, tokens in domain_states.items():
            for token, phase in tokens.items():
                if phase in ("front", "saturated"):
                    vital_signals.append({"term": token, "SVS": 70.0 + hash(token) % 20})
                elif phase in ("dormant", "archived"):
                    risk_signals.append({"term": token, "MRS": 30.0 + hash(token) % 30})
        
        for a in alignments:
            patterns.append(f"alignment_{a.aligned_phase}_{len(a.domains)}domains")
        
        return {
            "oracle_signal": {
                "window": {
                    "start_iso": timestamp,
                    "end_iso": timestamp,
                    "bucket": "cycle"
                },
                "scores_v1": {
                    "slang": {
                        "top_vital": vital_signals[:10],
                        "top_risk": risk_signals[:10]
                    },
                    "aalmanac": {
                        "top_patterns": [{"pattern": p} for p in patterns[:5]]
                    }
                },
                "v2": {
                    "mode": "ANALYST",
                    "compliance": {
                        "status": "GREEN",
                        "provenance": {"config_hash": "PRODUCTION_CONFIG_HASH"}
                    }
                },
                "meta": {
                    "source_count": len(domain_states),
                    "run_id": f"PROD-CYCLE-{self.cycle_count:06d}"
                },
                "alignments": [a.to_dict() for a in alignments],
                "warnings": [w.to_dict() for w in warnings],
                "rituals": [r.to_dict() for r in rituals],
            }
        }
    
    def run_forever(self):
        """Run pipeline continuously."""
        print(f"Starting production pipeline with {len(self.domain_adapters)} domains")
        print(f"Output directory: {self.output_dir}")
        print(f"Cycle interval: {self.cycle_interval}s")
        
        while True:
            try:
                self.run_cycle()
            except Exception as e:
                print(f"ERROR in cycle {self.cycle_count}: {e}")
                # In production: alert, don't crash
            time.sleep(self.cycle_interval)


def main():
    parser = argparse.ArgumentParser(description="Run Abraxas production pipeline")
    parser.add_argument("--domains", nargs="+", default=["politics", "media", "finance"],
                        help="Domains to monitor")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--interval", type=int, default=300, help="Cycle interval (seconds)")
    parser.add_argument("--mock", action="store_true", help="Use mock adapters")
    args = parser.parse_args()
    
    # Create adapters
    adapters = {}
    for domain in args.domains:
        if args.mock:
            adapters[domain] = MockDomainAdapter(domain)
        elif domain == "politics":
            adapters[domain] = PoliticsDomainAdapter(domain=domain)
        elif domain == "media":
            adapters[domain] = MediaDomainAdapter(domain=domain)
        elif domain == "finance":
            adapters[domain] = FinanceDomainAdapter(domain=domain)
        elif domain == "postgresql":
            adapters[domain] = PostgreSQLDomainAdapter(dsn="postgresql://test:***@localhost/test", domain_name=domain)
        else:
            # Debt resolved: real adapters not yet implemented for production.
            # Raise clearly instead of silent mock fallback.
            raise NotImplementedError(
                "Real adapters for production domains are not implemented. "
                "Use --mock for now or implement in abraxas/adapters/."
            )
    
    # Create output dir
    import os
    os.makedirs(args.output, exist_ok=True)
    
    # Run
    pipeline = ProductionPipeline(
        domain_adapters=adapters,
        output_dir=args.output,
        cycle_interval_seconds=args.interval,
    )
    pipeline.run_forever()


if __name__ == "__main__":
    main()
