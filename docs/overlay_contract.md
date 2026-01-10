# Overlay Contract

Every optional overlay must satisfy all gates below to preserve determinism and import isolation.

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
