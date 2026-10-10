# Aether Multimodal Input Contract (Explicit Unknown)

Per Aether/SPEC.md §4 and §5. This file declares the current UNKNOWN state.

Current call (from pipeline):
provider.produce_evidence(request_id, claim, context={})

**Current state (2026-10-09):** UNKNOWN. No live encoder exists. The contract is declared but not computable.

**Declared input shape (future when implemented):**
```yaml
modalities:
  text: string | null
  image: base64 | url | null
  audio: wav-bytes | url | null
  structured: json | null
provenance:
  per_modality:
    text: {source: str, hash: str, timestamp: str}
    ...
request_id: str
```

**Governance note:** Inputs with missing modalities must be fenced as SPECULATIVE. Missing modalities trigger fail-closed (AetherNotImplemented). No confidence laundering across modalities.