# {{ engine_name }}

{{ description }}

## Purpose
{{ purpose }}

## Evidence Type
`{{ evidence_type }}`

## Installation
```bash
pip install -e .[dev]
```

## Development
```bash
make test          # Run tests
make lint          # Run ruff + mypy
make build         # Build wheel
make publish       # Publish to PyPI
```

## Abraxas Integration
```python
from {{ engine_name }}.compat.abraxas import {{ EngineName }}EvidenceProvider
from abraxas.evidence.provider import ProviderRegistry

registry = ProviderRegistry()
registry.register({{ EngineName }}EvidenceProvider())
```

## Compute Profile
- **Profile**: {{ compute_profile }}
- **GPU Memory**: {{ gpu_memory_gb }} GB

## Model Checkpoints
Stored on HuggingFace Hub: `scrimshawlife-ctrl/{{ engine_name }}-checkpoints`

## Artifacts
Stored on Neon: `neon://{{ engine_name }}/`

## License
MIT
