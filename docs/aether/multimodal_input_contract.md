# Aether Multimodal Input Contract (Explicit Unknown)

Per Aether/SPEC.md §4 and §5. This file declares the current UNKNOWN state.

Current call (from pipeline):
provider.produce_evidence(request_id, claim, context={})

Proposed future shape (to be filled only on real consumer):
context = {
  "modalities": {
    "text": "...",
    "image": "path or bytes",
    "audio": "...",
    "structured": {...}
  },
  "provenance": {...}
}