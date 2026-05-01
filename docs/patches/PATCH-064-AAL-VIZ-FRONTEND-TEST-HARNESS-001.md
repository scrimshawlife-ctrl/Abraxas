# PATCH-064 — AAL-VIZ-FRONTEND-TEST-HARNESS-001

## purpose
Enable deterministic frontend test execution for `frontend/aal-viz` with a minimal harness manifest proving harness state.

## authority boundary
Verification-only surface. No runtime behavior changes to visualization artifacts, no interaction enablement, and no animation/runtime activation.

## frontend harness
Adds `package.json`, `vitest.config.ts`, and `tsconfig.json` for reproducible test execution with `vitest` + `jsdom`.

## deterministic guarantees
Harness manifest hashes harness files and emits stable `manifest_id`/`manifest_hash` from canonical JSON.

## next patch
PATCH-065.
