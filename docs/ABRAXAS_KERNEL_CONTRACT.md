# ABRAXAS_KERNEL_CONTRACT (Canonical Hardening Layer)
Version: 0.1
Scope: Abraxas kernel spine (repo: scrimshawlife-ctrl/Abraxas)

## 0) Purpose
Abraxas is an always-on symbolic intelligence appliance: it detects symbolic/linguistic compression, generates memetic weather, runs deterministic scenario envelopes, and emits provenance-embedded artifacts.

This contract makes the implicit guarantees explicit:
- determinism
- provenance
- no hidden coupling
- detector purity (flagging, not rewriting reality)

## 1) Non-Negotiable Laws (Kernel-Level)
1. Determinism by default
   - Given identical inputs + config + model/version pins, outputs must be identical.
   - Randomness must be injected only through explicit, logged seeds.

2. Provenance-first artifacts
   - Every emitted artifact MUST carry a provenance bundle:
     - source hashes (SHA-256)
     - config snapshot hash
     - code version reference (git commit)
     - runtime environment signature (python/node versions)

3. Detector Purity Rule (Canon)
   - Detection modules may label, score, and annotate signals.
   - Detection modules MUST NOT censor, rewrite, block, “correct”, or suppress inputs/outputs.
   - Any optional “normalization” steps must be explicitly declared as a transform and logged as such.

4. ABX-Runes as only legal coupling layer
   - Cross-module calls MUST happen via rune invocation (capability registry).
   - Direct imports across modules are allowed only within the same module boundary.
   - No hidden coupling via shared globals, implicit env, or unregistered endpoints.

5. Governance gates for emergent metrics
   - New metrics begin in SHADOW mode (observe/log only).
   - Promotion to ACTIVE requires:
     - evidence bundle
     - reproducible evaluation
     - governance approval record

6. Append-only memory for time (AAlmanac)
   - Historical symbolic state is immutable: append-only writes.
   - Decay/half-life affects interpretation layers, never the stored record.

7. IPO (Incremental Patch Only) for evolution
   - Changes are additive; rewrites require explicit justification and migration notes.
   - “Complexity must pay rent”: each added layer must reduce a measurable metric
     (time/cost/entropy/compute/operational risk).

## 2) Canonical Data Planes
A) Signal Plane (inputs)
- Linguistic events, lexicon data, ingestion streams (e.g., Decodo API)

B) Feature Plane (detected measures)
- compression events (SCO/ECO)
- memetic drift signals (weather engine)
- scenario envelopes (SER)

C) Artifact Plane (outputs)
- deterministic reports, cascade sheets, advisories, dashboards
- each artifact includes provenance bundle

D) Memory Plane (AAlmanac)
- append-only temporal store of symbolic state

E) Capability Plane (ABX-Runes registry)
- rune → capability → implementation mapping
- stable interface for overlays and hot-swaps

## 3) Required Kernel Interfaces (Abstract)
- kernel.invoke(rune_id, payload, context) -> result + provenance
- kernel.emit(artifact_type, data, provenance) -> artifact_id
- kernel.record(almanac_event) -> almanac_id (append-only)
- kernel.govern(candidate_metric_event) -> status (shadow/candidate/promoted)

## 4) Repo Placement Guidance (Non-binding)
Suggested locations based on existing structure:
- /abx           : CLI + kernel runtime entrypoints
- /registry      : rune registry + capability mapping
- /scheduler     : ERS/runner scheduling integration
- /abraxas       : domain modules (compression, weather, SER)
- /server        : API surface (must call kernel.invoke)
- /systemd       : edge service wrappers (must preserve determinism/provenance)

## 5) Compliance Checklist (Pass/Fail)
- [ ] All cross-module calls go through rune invocations
- [ ] All artifacts carry provenance bundle
- [ ] All emergent metrics start SHADOW-only
- [ ] AAlmanac is append-only
- [ ] Detector purity enforced (no censor/rewrite)
- [ ] IPO discipline applied to all future changes
