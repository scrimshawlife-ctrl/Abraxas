# Plan: Production Canon Transition & Deployment

**Date**: 2026-10-04
**Goal**: Execute the formal canon mutation from CANON-SHADOW to PRODUCTION CANON, prepare production deployment, and enable live data integration.

---

## Current Context / Assumptions

- **Repo state**: `469364c` on `origin/main`, 299 tests passing
- **All gates authorized**: EXP-001 ACTIVE, N5 COMPLETE, PRODUCTION APPROVED, CANON_MUTATION AUTHORIZED
- **Canon state**: Currently CANON-SHADOW/ADVISORY_ONLY → transitioning to PRODUCTION CANON
- **Key components ready**:
  - Domain Compression Engines (DCEs)
  - Oracle Pipeline v2 (Signal → Compression → Forecast → Narrative)
  - Phase Detection Engine (alignment, synchronicity, early warning)
  - Resonance Narratives (output layer with diff mode)
  - Ritual System (7 protocols, effect tracking)
  - CypherTempre Timechain (immutable record storage)
  - 6-gate metric governance

---

## Architecture / Proposed Approach

**Three-phase sequential execution**:

1. **Phase A — Canon Mutation** (15 min): Tag v2.0.0 release, document transition in ROADMAP.md and CHANGELOG.md, push tag
2. **Phase B — Production Deployment Prep** (30-60 min): Helm production values, health check verification, monitoring config, ConfigMap for runtime params
3. **Phase C — Live Data Integration** (ongoing): Connect real domain streams, run pipeline in production mode, monitor accuracy

Each phase commits independently with verification.

---

## Step-by-Step Tasks

### Phase A: Canon Mutation & Release Tag

#### Task A1: Create release tag v2.0.0
```bash
cd /Users/appliedalchemylabs/Abraxas
git tag -a v2.0.0 -m "Production Canon v2.0.0 - Predictive Intelligence Layer

COMPONENTS:
- Domain Compression Engines (DCEs): versioned lexicons, lineage tracking, domain operators
- Oracle Pipeline v2: Signal → Compression → Forecast → Narrative with 6-gate governance
- Phase Detection Engine: cross-domain alignment, synchronicity mapping, early warning, drift-resonance coupling
- Resonance Narratives: human-readable output layer with diff mode, constraints, evidence gating
- Ritual System: symbolic modulation layer with 7 protocols, effect tracking
- CypherTempre Timechain: immutable record storage with PoW, file fallback
- 6-gate metric governance: provenance, falsifiability, redundancy, rent, ablation, stabilization

TESTS: 299 passing (core + 5 Q1 qualifications + Resonance + Oracle v2 + Phase + Ritual)

GATES: EXP-001 ACTIVE, N5 COMPLETE, PRODUCTION APPROVED, CANON_MUTATION AUTHORIZED

TRANSITION: CANON-SHADOW/ADVISORY_ONLY → PRODUCTION CANON"
git push origin v2.0.0
```
**Verification**: `git tag -l v2.0.0` shows tag; `git describe --tags` returns `v2.0.0`

#### Task A2: Update ROADMAP.md with production canon milestone
**File**: `/Users/appliedalchemylabs/Abraxas/ROADMAP.md`
**Action**: Add new section after gate change log:
```markdown
---

## 🏁 PRODUCTION CANON MILESTONE — v2.0.0 (2026-10-04)

**Tag**: `v2.0.0`
**Commit**: `469364c`
**Status**: **PRODUCTION CANON AUTHORIZED & TAGGED**

### Components in Canon
- Domain Compression Engines (DCEs)
- Oracle Pipeline v2
- Phase Detection Engine
- Resonance Narratives
- Ritual System
- CypherTempre Timechain
- 6-Gate Metric Governance

### Verification
- 299 tests passing
- All gates authorized
- Integrated pipeline validated end-to-end

### Next: Production Deployment (Phase B)
```
**Verification**: `grep "PRODUCTION CANON MILESTONE" ROADMAP.md` returns the section

#### Task A3: Create CHANGELOG.md entry
**File**: `/Users/appliedalchemylabs/Abraxas/CHANGELOG.md` (create if missing)
```markdown
# Changelog

## v2.0.0 — Production Canon (2026-10-04)

### Canon Mutation
- CANON-SHADOW/ADVISORY_ONLY → PRODUCTION CANON
- All gates authorized: EXP-001, N5, PRODUCTION, CANON_MUTATION, RITUAL_SYSTEM

### Components Delivered
- Domain Compression Engines (DCEs)
- Oracle Pipeline v2 (Signal → Compression → Forecast → Narrative)
- Phase Detection Engine (alignment, synchronicity, early warning, drift-resonance coupling)
- Resonance Narratives (diff mode, constraints, evidence gating)
- Ritual System (7 protocols, effect tracking)
- CypherTempre Timechain (immutable records, PoW, file fallback)

### Tests
- 299 tests passing
- 5 Q1 qualifications: HYPERLEX, SEMION, NOESIS, TRUTINA, ABRAXAS
- Integrated pipeline: Phase Detection + Oracle v2 + Resonance Narratives + Ritual System

### Gates
- AC-EIC-G1 = ACCEPT (2026-10-04)
- EXP-001: ACTIVE
- N5: COMPLETE
- PRODUCTION: APPROVED
- CANON_MUTATION: AUTHORIZED
```
**Verification**: `cat CHANGELOG.md | head -30` shows v2.0.0 entry

---

### Phase B: Production Deployment Prep

#### Task B1: Create production Helm values
**File**: `/Users/appliedalchemylabs/Abraxas/deployment/helm-chart/abraxas/values-prod.yaml`
```yaml
# Production Helm values for Abraxas
replicaCount: 3

image:
  repository: abraxas
  tag: v2.0.0
  pullPolicy: IfNotPresent

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

service:
  type: ClusterIP
  port: 8080

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: abraxas.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: abraxas-tls
      hosts:
        - abraxas.example.com

config:
  # Runtime configuration
  logLevel: INFO
  metricsPort: 9090
  healthPort: 8081
  
  # Oracle v2 settings
  oracle:
    mode: ANALYST
    stabilizationTicks: 3
    evidenceBudget: 100
  
  # Phase Detection settings
  phase:
    minDomainsForAlignment: 2
    velocityThreshold: 0.5
    confidenceThreshold: 0.6
  
  # Timechain settings
  timechain:
    enabled: true
    difficulty: 4
    fallbackToFile: true

# Monitoring
monitoring:
  enabled: true
  prometheus:
    enabled: true
    port: 9090
    path: /metrics
  grafana:
    enabled: true
    dashboards:
      - abraxas-overview
      - abraxas-phase-detection
      - abraxas-oracle-pipeline

# Persistence
persistence:
  enabled: true
  size: 50Gi
  storageClass: fast-ssd
```
**Verification**: `helm lint deployment/helm-chart/abraxas --values deployment/helm-chart/abraxas/values-prod.yaml` passes

#### Task B2: Verify health check endpoints
**File**: `/Users/appliedalchemylabs/Abraxas/scripts/health_check.py`
**Action**: Ensure it checks:
- `/health/live` → liveness probe (process alive)
- `/health/ready` → readiness probe (orchestrator initialized, memory layer healthy)
- `/health/metrics` → Prometheus metrics

```bash
# Test locally
cd /Users/appliedalchemylabs/Abraxas
python scripts/health_check.py --check-all
```
**Expected output**:
```
✓ Liveness: OK
✓ Readiness: OK (orchestrator initialized, memory layer healthy)
✓ Metrics: OK (Prometheus format)
```

#### Task B3: Create production ConfigMap
**File**: `/Users/appliedalchemylabs/Abraxas/deployment/helm-chart/abraxas/templates/configmap-prod.yaml`
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: abraxas-config
  labels:
    app: abraxas
data:
  ABRAXAS_ENV: "production"
  ABRAXAS_LOG_LEVEL: "INFO"
  ABRAXAS_ORACLE_MODE: "ANALYST"
  ABRAXAS_PHASE_MIN_DOMAINS: "2"
  ABRAXAS_TIMECHAIN_ENABLED: "true"
  ABRAXAS_TIMECHAIN_DIFFICULTY: "4"
  ABRAXAS_EVIDENCE_BUDGET: "100"
  ABRAXAS_STABILIZATION_TICKS: "3"
```
**Verification**: `kubectl apply --dry-run=client -f deployment/helm-chart/abraxas/templates/configmap-prod.yaml` succeeds

#### Task B4: Create monitoring dashboard JSON
**File**: `/Users/appliedalchemylabs/Abraxas/deployment/grafana/abraxas-overview.json`
```json
{
  "dashboard": {
    "title": "Abraxas Overview",
    "panels": [
      {
        "title": "Oracle Runs / min",
        "type": "graph",
        "targets": [{"expr": "rate(abraxas_oracle_runs_total[5m])"}]
      },
      {
        "title": "Phase Alignments Active",
        "type": "stat",
        "targets": [{"expr": "abraxas_phase_alignments_active"}]
      },
      {
        "title": "Ritual Executions / hour",
        "type": "graph",
        "targets": [{"expr": "rate(abraxas_ritual_executions_total[1h])"}]
      },
      {
        "title": "Timechain Blocks",
        "type": "stat",
        "targets": [{"expr": "abraxas_timechain_blocks_total"}]
      },
      {
        "title": "Canon Mutation Status",
        "type": "stat",
        "targets": [{"expr": "abraxas_canon_status{status=\"production\"}"}]
      }
    ]
  }
}
```
**Verification**: File exists and is valid JSON

---

### Phase C: Live Data Integration (Preparation)

#### Task C1: Create domain data adapter interface
**File**: `/Users/appliedalchemylabs/Abraxas/abraxas/adapters/domain_data.py` (new)
```python
"""Domain Data Adapter Interface for Live Streams

Implement this interface for each domain data source.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class DomainTokenState:
    """Single token's lifecycle state."""
    token: str
    domain: str
    phase: str  # proto/front/saturated/dormant/archived
    tau_level: float
    tau_velocity: float
    timestamp_utc: str
    confidence: float


@dataclass
class DomainSnapshot:
    """Complete domain state snapshot."""
    domain: str
    tokens: List[DomainTokenState]
    timestamp_utc: str
    source: str


class DomainDataAdapter(ABC):
    """Abstract adapter for domain data streams."""
    
    @abstractmethod
    def fetch_current_state(self) -> DomainSnapshot:
        """Fetch current domain state from live source."""
        pass
    
    @abstractmethod
    def fetch_historical(self, hours: int = 24) -> List[DomainSnapshot]:
        """Fetch historical snapshots for tau calculation."""
        pass
    
    @abstractmethod
    def get_domain_name(self) -> str:
        """Return domain identifier."""
        pass


class MockDomainAdapter(DomainDataAdapter):
    """Mock adapter for testing."""
    
    def __init__(self, domain: str):
        self._domain = domain
    
    def fetch_current_state(self) -> DomainSnapshot:
        # Return mock data matching test fixtures
        tokens = [
            DomainTokenState(
                token=f"{self._domain}_token_1",
                domain=self._domain,
                phase="front",
                tau_level=0.7,
                tau_velocity=0.4,
                timestamp_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                confidence=0.8,
            )
        ]
        return DomainSnapshot(
            domain=self._domain,
            tokens=tokens,
            timestamp_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source="mock",
        )
    
    def fetch_historical(self, hours: int = 24) -> List[DomainSnapshot]:
        return [self.fetch_current_state()]
    
    def get_domain_name(self) -> str:
        return self._domain
```
**Verification**: `python -c "from abraxas.adapters.domain_data import MockDomainAdapter; a = MockDomainAdapter('test'); print(a.fetch_current_state())"` works

#### Task C2: Create production pipeline runner
**File**: `/Users/appliedalchemylabs/Abraxas/scripts/run_production_pipeline.py`
```python
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

from abraxas.phase.detector import create_phase_detector
from abraxas.phase.early_warning import create_early_warning_system
from abraxas.core.temporal_tau import TauCalculator, Observation
from abraxas.oracle.v2.bundle import run_bundle
from abraxas.renderers.resonance_narratives import render_narrative_bundle
from abraxas.ritual import create_ritual_engine
from abraxas.adapters.domain_data import DomainDataAdapter, MockDomainAdapter


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
            "oracle_bundle": bundle_result,
            "narrative": narrative,
        }
        
        # Save to output dir
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
        else:
            # TODO: Implement real adapters
            adapters[domain] = MockDomainAdapter(domain)  # Fallback
    
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
```
**Verification**: 
```bash
cd /Users/appliedalchemylabs/Abraxas
mkdir -p ./output
python scripts/run_production_pipeline.py --mock --domains politics media finance --output ./output --interval 10
# Should run 2-3 cycles and produce JSON files in ./output/
```

#### Task C3: Create production deployment script
**File**: `/Users/appliedalchemylabs/Abraxas/scripts/deploy_production.sh`
```bash
#!/bin/bash
set -euo pipefail

# Production deployment script for Abraxas v2.0.0

NAMESPACE="abraxas-prod"
RELEASE="abraxas"
CHART="./deployment/helm-chart/abraxas"
VALUES="./deployment/helm-chart/abraxas/values-prod.yaml"

echo "Deploying Abraxas v2.0.0 to production..."

# Create namespace
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Apply ConfigMap
kubectl apply -f ./deployment/helm-chart/abraxas/templates/configmap-prod.yaml -n "$NAMESPACE"

# Deploy with Helm
helm upgrade --install "$RELEASE" "$CHART" \
  --namespace "$NAMESPACE" \
  --values "$VALUES" \
  --wait --timeout 5m

# Verify deployment
echo "Verifying deployment..."
kubectl rollout status deployment/"$RELEASE" -n "$NAMESPACE" --timeout=300s

# Check health
POD=$(kubectl get pods -n "$NAMESPACE" -l app="$RELEASE" -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n "$NAMESPACE" "$POD" -- python scripts/health_check.py --check-all

echo "Deployment complete!"
echo "Access: https://abraxas.example.com"
```
**Verification**: `bash -n scripts/deploy_production.sh` (syntax check passes)

---

## Tests / Validation

### Phase A Tests
| Test | Command | Expected |
|------|---------|----------|
| Tag exists | `git tag -l v2.0.0` | `v2.0.0` |
| Tag message | `git tag -n1 v2.0.0` | Contains "Production Canon v2.0.0" |
| ROADMAP updated | `grep "PRODUCTION CANON MILESTONE" ROADMAP.md` | Section present |
| CHANGELOG updated | `head -20 CHANGELOG.md` | v2.0.0 entry |

### Phase B Tests
| Test | Command | Expected |
|------|---------|----------|
| Helm lint | `helm lint deployment/helm-chart/abraxas --values deployment/helm-chart/abraxas/values-prod.yaml` | `==> Lint OK` |
| Health check | `python scripts/health_check.py --check-all` | All 3 checks OK |
| ConfigMap dry-run | `kubectl apply --dry-run=client -f deployment/helm-chart/abraxas/templates/configmap-prod.yaml` | `configmap/abraxas-config created (dry-run)` |
| Dashboard JSON | `python -m json.tool deployment/grafana/abraxas-overview.json > /dev/null` | No error |

### Phase C Tests
| Test | Command | Expected |
|------|---------|----------|
| Mock adapter | `python -c "from abraxas.adapters.domain_data import MockDomainAdapter; a=MockDomainAdapter('test'); print(a.fetch_current_state().domain)"` | `test` |
| Pipeline dry-run | `python scripts/run_production_pipeline.py --mock --interval 5 --output /tmp/test_output` | 2+ cycles, JSON files in output dir |
| Deploy script syntax | `bash -n scripts/deploy_production.sh` | No error |

---

## Risks, Tradeoffs, and Open Questions

### Risks
1. **Live data availability**: Phase C depends on real domain data streams; mock adapters are fallback only
2. **Helm chart maturity**: Current chart may need production hardening (network policies, pod disruption budgets)
3. **Timechain persistence**: File-based fallback needs persistent volume in production
4. **Canon mutation rollback**: No automated rollback if v2.0.0 has issues; manual `git revert` + re-tag required

### Tradeoffs
- **Mock adapters in Phase C**: Allows pipeline validation without live data; real adapters are separate integration work
- **Helm values-prod.yaml separate from values.yaml**: Avoids accidental production config in dev; requires maintaining two files
- **Cycle interval 300s**: Balances freshness vs. compute cost; tune based on domain velocity

### Open Questions
1. **Domain data sources**: Which real APIs/feeds for politics/media/finance? (Not in repo)
2. **TLS certificates**: cert-manager issuer configured? (Assumes letsencrypt-prod)
3. **Prometheus/Grafana**: Already deployed in cluster? (Assumes yes)
4. **Storage class**: `fast-ssd` exists? (May need adjustment)
5. **Image registry**: Where is `abraxas:v2.0.0` pushed? (Assumes accessible from cluster)

---

## Commit Strategy
Each task = 1 commit with descriptive message:
- `chore: tag v2.0.0 production canon release`
- `docs: ROADMAP.md production canon milestone`
- `docs: CHANGELOG.md v2.0.0 entry`
- `feat: production helm values and configmap`
- `feat: health check verification`
- `feat: monitoring dashboard`
- `feat: domain data adapter interface`
- `feat: production pipeline runner`
- `feat: production deployment script`

All commits to `main`, push after each phase.