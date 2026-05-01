# PATCH-064C — Frontend Registry Provisioning

## Purpose
Capture deterministic environment provisioning state for AAL-Viz frontend.

## Key Behavior
- Records npm registry configuration
- Records dependency lock presence
- Classifies npm failures as:
  - failed_environment
  - failed_code
- NEVER executes npm inside tests

## E403 Case
If npm ci fails:
- `npm_ci_status: failed_environment`
- `npm_ci_reason: npm_registry_e403_access_restricted`
- `frontend_execution: not_computable_environment`

## Approved Execution
```bash
cd frontend/aal-viz
npm ci
npm test
```

## Gate
PATCH-066 is blocked until execution is verified.

## Authority
No runtime, no interaction, no mutation.
