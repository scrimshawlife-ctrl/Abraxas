# Fusion Policy Constraints (from /Users/appliedalchemylabs/Aether/SPEC.md §4)

1. **Weakest-link only**: The fused confidence is the min across present modalities. No boosting from one strong modality to cover a weak one.
2. **Per-modality provenance mandatory**: Every modality contribution carries its own source, hash, timestamp, and adapter id.
3. **Speculative lane fenced**: Any input marked SPECULATIVE (e.g. future or inferred) must carry explicit NOT_COMPUTABLE flag and be excluded from canonical output.
4. **Fail closed on missing modalities**: If a required modality is absent or the encoder is not present, the entire call raises AetherNotImplemented. No partial results.
5. **Identity excludes wall-clock data**: engine_version and model_identity must be stable across runs; timestamps live only in provenance.

**Current state (2026-10-09):** These constraints are declared but not enforced in code because the engine does not exist. The aether provider deliberately raises to uphold the boundary.