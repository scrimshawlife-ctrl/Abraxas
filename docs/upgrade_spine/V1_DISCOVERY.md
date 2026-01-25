<!-- docs/upgrade_spine/V1_DISCOVERY.md -->
<!-- abraxas/evolution/candidate_generator.py: Deterministic generator for metric/operator/param tweak candidates based on domain deltas. -->
<!-- abraxas/evolution/store.py: Persistent store + hash-chained ledgers for evolution candidates, sandbox results, and promotions. -->
<!-- abraxas/evolve/evogate_builder.py: Builds EvoGate reports that evaluate proposal packs and recommend promotion. -->
<!-- abraxas/evolve/rune_adapter.py: Deterministic wrappers for EvoGate and related builders with provenance envelopes. -->
<!-- data/evolution/candidates/: JSON files holding evolution candidates emitted by the evolution track. -->
<!-- out/evolution_ledgers/candidates.jsonl: Append-only ledger recording evolution candidate events. -->

<!-- abraxas/evolve/ledger.py: Append-only, hash-chained JSONL ledger writer used by evolution tooling. -->
<!-- abraxas/core/provenance.py: Canonical hashing + provenance helpers for deterministic IDs and fingerprints. -->
<!-- docs/canon/ABRAXAS_CANON_LEDGER.txt: Canon ledger definition describing write-once evolution tracking and promotion constraints. -->
<!-- schemas/acceptance/v1/acceptance_status.schema.json: Acceptance schema used by the invariance gate. -->

<!-- tools/acceptance/run_acceptance_suite.py: Canonical 12-run invariance + safety gates for release readiness. -->
<!-- tests/test_evolve_ledger_rune.py: Golden/determinism tests for evolution ledger append behavior. -->
<!-- tests/test_evolution_system.py: End-to-end tests for candidate generation, sandboxing, and promotion gating. -->
<!-- tests/test_oracle_v2_evidence_convention_goldens.py: Golden evidence conventions for oracle v2 provenance stability. -->
<!-- tests/test_evolve_non_truncation_rune.py: Non-truncation gate tests for evolution pipeline safety. -->

<!-- tools/generate_patch_suggestions.py: Generates patch suggestions artifacts with deterministic output directories. -->
<!-- tools/summarize_migration_queue.py: Summarizes migration queue from ledger JSONL inputs. -->
<!-- tools/acceptance/run_acceptance_suite.py: Runs invariance + schema gates and writes ledger artifacts for audit. -->
