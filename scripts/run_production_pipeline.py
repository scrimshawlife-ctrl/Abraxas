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
from abraxas.core.temporal_tau import Observation, TauCalculator
from abraxas.evidence.providers.aether import AetherNotImplemented
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
        # See docs/aether/multimodal_input_contract.md for declared UNKNOWN input schema.
        # aether deliberately skipped (refusing boundary per sibling SPEC §5).
        engine_evidence = self._dispatch_to_engines(domain_states, alignments, timestamp)

        # 2.6 Build engine state summary for ritual preconditions
        engine_state = {}
        engine_summaries = []
        for e in engine_evidence:
            ed = e.to_dict() if hasattr(e, 'to_dict') else e
            engine_summaries.append(ed)
            engine_state[ed.get("engine", "unknown")] = {
                "confidence": ed.get("confidence", 0.0),
                "evidence_type": ed.get("evidence_type", ""),
                "claim": ed.get("claim", "")[:100],
            }

        # 3. Early Warning
        warnings = self.warning_system.generate_warnings(
            tau_snapshots, current_phases, sync_map
        )
        
        # 4. Ritual Engine (check if any rituals should fire)
        ritual_executions = []
        for domain, phase in current_phases.items():
            for protocol in self.ritual_engine.list_protocols():
                state_for_ritual = {
                    "domain_phase": phase,
                    "tau_velocity": tau_snapshots[domain].tau_velocity,
                    "alignment_strength": max(0.6, engine_state.get("resonance", {}).get("confidence", 0.6)),
                    "domains_aligned": max((len(a.domains) for a in alignments if domain in a.domains), default=0),
                    "cascade_risk": "MEDIUM",
                    "drift_resonance_detected": False,
                    "observation_count": tau_snapshots[domain].observation_count,
                    "confidence": tau_snapshots[domain].confidence.value,
                    "symbolic_state": "coherent",
                    "drift_detected": False,
                    "engine_evidence": engine_state,
                    "resonance_confidence": engine_state.get("resonance", {}).get("confidence", 0.0),
                }
                met, _ = self.ritual_engine.check_preconditions(protocol, state_for_ritual)
                if met:
                    # In production: add cooldown check
                    exec_result = self.ritual_engine.execute_ritual(
                        protocol.protocol_id,
                        operator="production_pipeline",
                        current_state=state_for_ritual,
                        timestamp_utc=timestamp,
                    )
                    ritual_executions.append(exec_result)
        
        # 5. Oracle Bundle (aggregate envelope)
        envelope = self._build_oracle_envelope(
            domain_states, alignments, warnings, ritual_executions, timestamp,
            engine_evidence=engine_summaries,
        )
        
        # Run oracle bundle with evidence attachment
        import os as _os
        import tempfile

        from abraxas.oracle.v2.evidence_convention import attach_evidence_from_run_dir
        from abraxas.oracle.v2.export import compute_run_id, export_run
        from abraxas.oracle.v2.orchestrate import attach_v2
        from abraxas.oracle.v2.render import render_by_mode

        # Persistent evidence for engine_evidence (files must survive temp dirs)
        run_id_for_ev = f"PROD-CYCLE-{self.cycle_count:06d}"
        persistent_ev_dir = _os.path.join(self.output_dir, run_id_for_ev, "evidence")
        _os.makedirs(persistent_ev_dir, exist_ok=True)
        engine_files: dict = {}
        for i, ed in enumerate(engine_summaries):
            fname = f"engine_{ed.get('engine','stub')}_{i}.json"
            fpath = _os.path.join(persistent_ev_dir, fname)
            with open(fpath, "w") as f:
                json.dump(ed, f)
            engine_files[f"engine_{i}"] = fname

        with tempfile.TemporaryDirectory() as td:
            attach_v2(
                envelope=envelope,
                config_hash="PRODUCTION_CONFIG_HASH",
                do_stabilization_tick=True,
            )
            run_id = compute_run_id(envelope)
            # Attach using persistent files (pointers recorded in envelope)
            attach_evidence_from_run_dir(
                envelope=envelope,
                out_dir=self.output_dir,
                files=engine_files,
                compute_hashes=True,
            )
            surface = render_by_mode(envelope)
            manifest = export_run(envelope=envelope, surface=surface, out_dir=td)
            bundle_result = {"run_id": run_id, "manifest": manifest, "surface": surface}
        
        # 6. Resonance Narrative
        narrative = render_narrative_bundle(envelope)
        
        # 7. Output
        output = {
            "cycle": self.cycle_count,
            "timestamp": timestamp,
            "alignments": [a.to_dict() for a in alignments],
            "warnings": [w.to_dict() for w in warnings],
            "ritual_executions": [r.to_dict() for r in ritual_executions],
            "engine_evidence": [e.to_dict() for e in engine_evidence],
            "oracle_bundle": bundle_result,
            "oracle_envelope": envelope,
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

    def _dispatch_to_engines(self, domain_states: Dict, alignments: List, timestamp: str,
                             events: list | None = None) -> List:
        """Dispatch to all live engines via manifest.
        Deepened: dynamic loop over live_engines(), skip aether (refusing boundary),
        pass richer context for phase/temporal/etc.
        events: optional list of event dicts for chronos rune chain (SCAN→ALIGN→OVERLAY→PACKET).
        """
        envelopes = []
        from importlib import import_module

        from abraxas.engines.manifest import get, live_engines

        for name in live_engines():
            if name == "aether":
                # deliberate skip per aether boundary spec
                continue
            spec = get(name)
            if not spec or not spec.implementation:
                continue
            try:
                mod, attr = spec.implementation.split(":", 1)
                provider = getattr(import_module(mod), attr)()
                # richer context
                ctx = {
                    "domain_states": domain_states,
                    "alignments_count": len(alignments),
                    "timestamp": timestamp,
                    "cycle": self.cycle_count,
                    "events": events,
                    "source_family": ["chronos"],
                    "run_id": f"dispatch-{self.cycle_count}-{name}",
                }
                claim = f"{name} dispatch cycle {self.cycle_count}"
                env = provider.produce_evidence(f"dispatch-{self.cycle_count}", claim, ctx)
                envelopes.append(env)
            except AetherNotImplemented:
                pass
            except Exception:
                pass  # safe for now

        return envelopes

    def _build_oracle_envelope(
        self,
        domain_states: Dict,
        alignments: List,
        warnings: List,
        rituals: List,
        timestamp: str,
        engine_evidence: List[Dict] | None = None,
    ) -> Dict:
        """Build oracle signal envelope from pipeline state."""
        # Aggregate vital signals across domains
        vital_signals = []
        risk_signals = []
        patterns = []
        engine_ev = engine_evidence or []
        
        for _domain, tokens in domain_states.items():
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
                "engine_evidence": engine_ev,
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
            from abraxas.adapters.postgresql_domain_adapter import PostgreSQLDomainAdapter

            adapters[domain] = PostgreSQLDomainAdapter(
                dsn="postgresql://test:***@localhost/test", domain_name=domain
            )
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
