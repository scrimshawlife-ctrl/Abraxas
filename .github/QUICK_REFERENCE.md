# Quick Reference for AI Assistants

**Ultra-condensed guide for ChatGPT and other AI assistants**

---

## What is Abraxas?
Symbolic intelligence system that detects linguistic compression (eggcorns), tracks memetic drift, runs as edge appliance. Think: **weather system for language**.

## Essential Files (Read in Order)
1. `README.md` — Overview
2. `CLAUDE.md` — Development guide (conventions, structure)
3. `.github/AI_ASSISTANT_GUIDE.md` — Detailed guide
4. `docs/canon/ABRAXAS_CANON_LEDGER.txt` — Design principles

## Core Principles
- **Determinism**: Same inputs → same outputs (ALWAYS)
- **Provenance**: SHA-256 hashes for everything
- **Write-Once**: Canonical data is immutable
- **No randomness** without fixed seeds

## Directory Structure
```
abraxas/          # Python core (operators, pipelines, CLI)
server/           # TypeScript Express server
client/           # React frontend
tests/            # pytest tests
docs/             # Specs, plans, canon
data/             # Input data
out/              # Output artifacts
```

## Key Modules
- `abraxas/core/` — Provenance, metrics, temporal tau
- `abraxas/operators/` — SCO/ECO symbolic operators
- `abraxas/linguistic/` — Phonetics, similarity, STI
- `abraxas/shadow_metrics/` — **LOCKED** (access via ϟ₇ only)
- `abraxas/runes/` — ABX-Runes symbolic operators

## Common Tasks

### Run Tests
```bash
pytest tests/           # Python
npm test                # TypeScript
```

### Add Python Module
1. Create `abraxas/mymodule/file.py`
2. Add tests `tests/test_file.py`
3. Include provenance tracking
4. Update `CLAUDE.md`

### Add API Endpoint
1. Add route in `server/routes.ts`
2. Add tests in `server/abraxas/tests/`

### Access Shadow Structural Metrics
```python
# ✅ CORRECT
from abraxas.runes.operators.sso import apply_sso
result = apply_sso({"symbol_pool": [...]})

# ❌ WRONG (raises AccessDeniedError)
from abraxas.shadow_metrics import compute_sei
```

## Git Workflow
- **Branch**: `claude/<description>-<session-id>` (session ID required!)
- **Commit**: `"Add feature description"`
- **Push**: `git push -u origin <branch>` (retry on failure: 2s, 4s, 8s, 16s)
- **PR**: `gh pr create --title "..." --body "..."`

## Conventions
**Python**: `snake_case` files, `PascalCase` classes, `snake_case` functions
**TypeScript**: `kebab-case` files, `PascalCase` classes, `camelCase` functions

## What NOT to Do
❌ Add randomness without seeds
❌ Skip provenance
❌ Mutate canonical data
❌ Access Shadow Metrics directly
❌ Over-engineer
❌ Push to main without PR

## Quick Commands
```bash
abx doctor              # System diagnostic
npm run dev             # Dev server
abx ui                  # UI server
pytest -v               # Verbose tests
grep -r "pattern" .     # Search code
```

## When Stuck
1. Check `CLAUDE.md`
2. Check `docs/specs/`
3. Look at tests
4. Read module docstrings

**Version**: 1.0.0 | **Last Updated**: 2025-12-29
