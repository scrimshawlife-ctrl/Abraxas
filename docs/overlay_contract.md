# Overlay Contract

Every optional overlay must satisfy all gates below to preserve determinism and import isolation.

## 0) Module vs overlay separation (hard boundary)
- **Modules** (e.g., AALmanac) live in core packages and must never import overlays.
- **Overlays** (e.g., Neon-Genie, BeatOven) are optional integrations that run through the overlay runtime.
- Core modules may read overlay outputs only via validated packets/registries, never via direct imports.
- Overlay-specific logic belongs in overlay packages or external repositories and must be dependency-isolated.

## A) Extras group
Each overlay ships as an optional dependency group in `pyproject.toml`.

Examples:
- `lens` (admin review UI)
- `aalmanac`
- `neongenie`
- `beatoven`
- `viz`
- `market`

## B) Deterministic diag gate
`abx diag deps` must emit deterministic, machine-parseable status lines.

Format:
- `deps: OK (core)`
- `deps: OK (lens)`
- `deps: MISSING (lens) missing=fastapi, uvicorn, jinja2, multipart -> install: pip install -e ".[lens]"`

## C) Help surface
- `abx --help` must list overlay namespaces.
- Overlay commands must print a friendly install message when deps are missing.

## D) Import isolation
- No overlay imports at core module import time.
- Overlay imports must occur inside command handlers after dependency checks.

## E) CI lanes
- Core lane runs without extras.
- Overlay lane runs with the specific extra installed.

## F) Overlay initialization workflow (template for all overlays)
Use this checklist when onboarding any new overlay (including Neon-Genie):

1. **Register the overlay**  
   - Add the overlay module path to `abraxas/overlays/dispatcher.py` `OVERLAY_REGISTRY`.  
   - Ensure the overlay exposes `run_overlay(inputs, ctx)` and returns an `overlay_packet.v0`.

2. **Define runtime availability**  
   - Ensure dependencies are isolated via `pyproject.toml` extras.  
   - Confirm `check_overlay_available()` discovers the overlay module.

3. **Enable via config**  
   - Add an entry to `overlays.v0.json` (via CLI or defaults) to toggle enablement.  
   - Confirm disabled overlays return deterministic `disabled` packets.

4. **Initialize in integration docs**  
   - Document the install command (extras group), required environment, and entry point.  
   - Include a minimal invocation example and expected packet schema.

5. **Governance gate**  
   - Validate `no_influence` / lane separation where applicable.  
   - Ensure overlay outputs never mutate core forecasts directly.

6. **Golden tests**  
   - Add a deterministic test with fixed inputs and a pinned output snapshot.
