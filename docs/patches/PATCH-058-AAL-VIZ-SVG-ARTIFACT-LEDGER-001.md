# PATCH-058 — AAL-VIZ-SVG-ARTIFACT-LEDGER-001

## purpose
Persist `AALVizCanarySVGRenderManifest.v1` into an append-only deterministic visual artifact ledger run.

## authority boundary
Render-ledger-only lane. No rendering, no inference, no activation, no rollback, no baseline mutation, no runtime config writes, no promotions, no scheduler loops, no external API calls.

## render artifact ledger role
Create and maintain canonical `AALVizSVGArtifactLedgerRun.v1` entries from render manifests while preserving prior reviewed entries exactly.

## dedupe behavior
Dedupes by `entry_id` only. Existing entries are preserved exactly and never overwritten; new entries are append-only.

## audit lineage
Each entry stores deterministic `render_manifest_hash` and `lineage_hash` from canonical hashing materials.

## no rendering / no mutation / no execution guarantee
The patch reads manifest and optional prior ledger, computes hashes, and writes ledger output only.

## next patch
PATCH-059 — AAL-VIZ-WEBGL-SCENE-SPEC-001.
