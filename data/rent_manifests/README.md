# Rent Manifests

This directory contains rent manifest files for Abraxas components.

## Purpose

Every metric, operator, and artifact in Abraxas must have a **rent manifest** that declares:
1. What it improves (measurable)
2. What it costs (time/compute/entropy)
3. How it's proven (tests + golden files + ledger deltas)

**No manifest = No merge.**

## Directory Structure

```
rent_manifests/
├── metrics/       # MetricRentManifest files
├── operators/     # OperatorRentManifest files
└── artifacts/     # ArtifactRentManifest files
```

## File Format

All manifests are YAML files following the canonical schema in:
`docs/specs/rent_manifest_schema.md`

## How to Add a New Manifest

See: `docs/plan/rent_enforcement_v0_1_patch_plan.md`

Quick steps:
1. Implement your component
2. Add tests + golden files
3. Create manifest YAML in appropriate directory
4. Run `python -m abraxas.cli.rent_check --strict true`
5. Fix any validation errors
6. Merge

## Validation

Run rent enforcement checks:
```bash
python -m abraxas.cli.rent_check --strict true
```

This validates all manifests and ensures complexity pays rent.
