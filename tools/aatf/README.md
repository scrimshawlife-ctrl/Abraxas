# AATF — Abraxas Admin & Training Forge

AATF v0.1.0 is a local-only, shadow-only admin/training forge for Abraxas.
It ingests documents, canonicalizes deterministically, chunks deterministically,
queues items for review, and exports governed artifacts for later promotion.

## What AATF is
- A deterministic ingest → queue → review → export toolchain.
- A local-only, shadow-only forge that never mutates oracle inference directly.

## What AATF is not
- A cloud pipeline.
- An auto-promotion mechanism into Abraxas/AAL weights.

## Local-only guarantee
All data is stored in `tools/aatf/.aatf/` and never leaves the machine.

## Shadow-only guarantee
Ingests and exports are isolated until explicitly promoted through governance.

## Quickstart
```bash
python -m aatf ingest <path>
python -m aatf queue list
python -m aatf review approve <item_id> --notes "..."
python -m aatf export bundle --types aalmanac,memetic_weather,neon_genie,rune_proposals
```

## Determinism notes
- Canonicalization normalizes unicode NFC, newlines, and whitespace.
- Chunk IDs are stable: sha256(canonical_text + ":" + start + ":" + end).
- Export bundles are deterministic zip files with fixed timestamps and sorted entries.
