# {{ EngineName }} Engine — {{ purpose }}

## Purpose
{{ purpose }}

## Evidence Type
`{{ evidence_type }}`

## Input Contract
```json
{
  "claim": "string",
  "context": {
    // Engine-specific context fields
  }
}
```

## Output Contract (EvidenceEnvelope)
- `evidence_type`: "{{ evidence_type }}"
- `candidate_outputs`: [...]
- `reasoning_steps`: [...]
- `provenance`: {model_identity, method, ...}

## Verification Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Compute Requirements
- **Profile**: {{ compute_profile }}
- **GPU Memory**: {{ gpu_memory_gb }} GB

## Model Checkpoints
HuggingFace Hub: `scrimshawlife-ctrl/{{ engine_name }}-checkpoints`

## Artifacts
Neon bucket: `neon://{{ engine_name }}/`

## Adapter Interface
`{{ EngineName }}EvidenceProvider` implementing `EvidenceProvider` with:
- `engine_name = "{{ engine_name }}"`
- `supported_evidence_types = [EvidenceType.{{ evidence_type }}]`
