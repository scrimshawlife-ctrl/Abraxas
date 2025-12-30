# AI Assistant Quick Start Guide for Abraxas

**For ChatGPT, Claude, and other AI assistants accessing this repository**

---

## 🎯 What You Need to Know Immediately

**Abraxas** is a production-grade **symbolic intelligence system** that:
- Detects linguistic compression patterns (eggcorns like "apex twin" → "aphex twin")
- Tracks memetic drift and lifecycle dynamics
- Operates as an always-on edge appliance with self-healing capabilities
- Generates **deterministic provenance** for every linguistic event

Think of it as a **weather system for language**.

---

## 📁 Essential Files to Read First

When you access this repo, start with these files in order:

1. **`README.md`** — Project overview, architecture, features
2. **`CLAUDE.md`** — Comprehensive development guide (conventions, module organization, workflows)
3. **`docs/canon/ABRAXAS_CANON_LEDGER.txt`** — Canonical design principles
4. **This file (`.github/AI_ASSISTANT_GUIDE.md`)** — You're reading it now

---

## 🏗️ Repository Structure Quick Reference

```
Abraxas/
├── abraxas/                    # Python core modules
│   ├── core/                   # Provenance, metrics, temporal tau
│   ├── operators/              # SCO/ECO symbolic operators
│   ├── linguistic/             # Phonetics, similarity, transparency
│   ├── cli/                    # Command-line tools
│   ├── lexicon/                # Lexicon engine v1
│   ├── oracle/                 # Oracle pipeline v1
│   ├── slang/                  # Slang analysis & AAlmanac
│   ├── integrity/              # D/M layer (information integrity)
│   ├── sod/                    # Second-Order Dynamics
│   ├── shadow_metrics/         # Shadow Structural Metrics (LOCKED)
│   ├── weather/                # Weather engine
│   ├── runes/                  # ABX-Runes symbolic operators
│   └── ...                     # Many more specialized modules
│
├── server/                     # TypeScript Express server
│   ├── index.ts                # Server entry point
│   ├── routes.ts               # API routes
│   └── abraxas/                # Abraxas server modules
│
├── client/                     # React frontend
│   └── src/                    # React components & pages
│
├── tests/                      # Python tests (pytest)
│   ├── fixtures/               # Test data
│   ├── golden/                 # Golden test references
│   └── shadow_metrics/         # Shadow Structural Metrics tests
│
├── docs/                       # Documentation
│   ├── canon/                  # Canonical principles
│   ├── specs/                  # Technical specifications
│   └── plan/                   # Implementation plans
│
├── data/                       # Data storage
├── out/                        # Output artifacts
└── examples/                   # Example code
```

---

## 🚦 Critical Design Principles (Read This!)

Abraxas follows **strict deterministic, provenance-first design**:

### 1. Determinism is MANDATORY
- Same inputs → same outputs (always)
- No `random()` without fixed seeds
- Stable sorting (explicit keys)
- No non-deterministic operations

### 2. Provenance is EVERYWHERE
- Every artifact includes SHA-256 hash
- Timestamps in ISO8601 with 'Z' timezone
- Full execution metadata tracked
- See `abraxas/core/provenance.py`

### 3. Write-Once, Annotate-Only
- Canonical data is **immutable**
- Modifications happen via **annotations** (append-only)
- Example: AAlmanac ledger (`abraxas/slang/`)

### 4. Anti-Hallucination
- Metrics are **contracts**, not ideas
- No hand-waving or approximation
- Evidence-based, reproducible outputs

### 5. SEED Framework Compliance
- **S**ignature-based provenance
- **E**xecution determinism
- **E**vent-level auditability
- **D**rift detection

---

## 🔑 Key Concepts You Must Understand

### SCO/ECO (Symbolic Compression Operator)
- **SCO**: General symbolic compression detection
- **ECO**: Eggcorn-specific compression (high phonetic similarity)
- Detects when opaque symbols → transparent substitutes
- Example: "aphex twin" (opaque) → "apex twin" (transparent)

### STI (Symbolic Transparency Index)
- Measures how "transparent" a symbol is (0.0 = opaque, 1.0 = transparent)
- Key metric in compression detection

### RDV (Replacement Direction Vector)
- Tracks affective/rhetorical shifts in symbolic replacements
- Dimensions: humor, aggression, authority, intimacy, nihilism, irony

### τ (Tau) Operator
- **τₕ**: Half-life (symbolic persistence)
- **τᵥ**: Velocity (emergence/decay rate)
- **τₚ**: Phase proximity (distance to lifecycle boundary)

### Shadow Structural Metrics (SSM) **[LOCKED MODULE]**
- **Six Cambridge Analytica-derived metrics**: SEI, CLIP, NOR, PTS, SCG, FVC
- **Observe-only**: NEVER influence other metrics
- **Access**: ONLY via ABX-Runes ϟ₇ (SSO) interface
- **See**: `docs/specs/shadow_structural_metrics.md`

### ABX-Runes
- Symbolic operator system with deterministic provenance
- Seven canonical runes: ϟ₁ (RFA), ϟ₂ (TAM), ϟ₃ (WSSS), ϟ₄ (SDS), ϟ₅ (IPL), ϟ₆ (ADD), ϟ₇ (SSO)
- Registry: `abraxas/runes/registry.json`

---

## 📖 Common Tasks & How to Do Them

### Task 1: Add a New Python Module

1. Create file in appropriate directory: `abraxas/mymodule/my_operator.py`
2. Add `__init__.py` if new package
3. Update `pyproject.toml` if needed
4. Add tests in `tests/test_my_operator.py`
5. Document in `CLAUDE.md` and relevant README

**Conventions**:
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case`
- Include provenance tracking
- Add type hints

### Task 2: Add a New API Endpoint

1. Add route in `server/routes.ts` or module-specific routes
2. Add TypeScript types in `shared/` if needed
3. Add tests in `server/abraxas/tests/`
4. Update API documentation

### Task 3: Add a New CLI Command

1. Create CLI module in `abraxas/cli/my_command.py`
2. Add entry point in `pyproject.toml` if needed
3. Use `argparse` for argument parsing
4. Include provenance and determinism

### Task 4: Work with Provenance

```python
from abraxas.core.provenance import Provenance, hash_canonical_json

# Create provenance
prov = Provenance(
    run_id=f"RUN-{uuid.uuid4().hex[:8]}",
    started_at_utc=Provenance.now_iso_z(),
    inputs_hash=hash_canonical_json(inputs),
    config_hash=hash_canonical_json(config)
)

# Include in output
output = {
    "result": my_result,
    "provenance": prov.__dict__
}
```

### Task 5: Run Tests

```bash
# Python tests
pytest tests/                           # All tests
pytest tests/test_oracle_runner.py      # Specific test
pytest -v                               # Verbose
pytest --cov=abraxas                    # With coverage

# TypeScript tests
npm test                                # All tests
npm run test:watch                      # Watch mode

# Smoke test
abx smoke                               # Quick sanity check
```

### Task 6: Access Shadow Structural Metrics

```python
# ✅ CORRECT: Via ABX-Runes ϟ₇
from abraxas.runes.operators.sso import apply_sso

result = apply_sso({
    "symbol_pool": [...],
    "time_window_hours": 24,
    "metrics_requested": ["SEI", "CLIP", "PTS"]
})

# ❌ WRONG: Direct access (will raise AccessDeniedError)
from abraxas.shadow_metrics import compute_sei  # FORBIDDEN
```

---

## 🔍 How to Find Information

### Quick Searches

**Finding a specific metric or operator**:
```bash
grep -r "STI\|Symbolic Transparency" abraxas/
grep -r "class.*Operator" abraxas/operators/
```

**Finding where a module is used**:
```bash
grep -r "from abraxas.oracle import" .
```

**Finding test examples**:
```bash
find tests/ -name "test_*.py" | xargs grep -l "oracle"
```

### Documentation Hierarchy

1. **`CLAUDE.md`** — Comprehensive development guide
2. **`docs/specs/`** — Technical specifications
3. **`docs/canon/`** — Canonical principles
4. **`README.md`** — Project overview
5. **Inline docstrings** — Code-level documentation

---

## ⚠️ Important Constraints & Rules

### Git Workflow

**Branch Naming**: MUST follow pattern `claude/<description>-<session-id>`
- Example: `claude/add-weather-engine-5XgrC`
- Session ID at end is REQUIRED for push authentication

**Commit Messages**: Clear, descriptive
- Prefix: Add, Fix, Refactor, Update, Remove, Docs, Test
- Example: `"Add temporal tau operator with confidence bands"`

**Pushing**: Use `-u origin <branch-name>` and retry on network failures
```bash
git push -u origin claude/my-feature-abc123
# Retry up to 4 times with exponential backoff (2s, 4s, 8s, 16s)
```

**Creating PRs**: Use `gh` CLI
```bash
gh pr create --title "Title" --body "Description"
```

### Code Conventions

**Python**:
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Use Pydantic for data models
- Include type hints
- Add docstrings

**TypeScript**:
- Files: `kebab-case.ts`
- Classes/Types: `PascalCase`
- Functions: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Use Zod for validation

### Testing

- **Python**: pytest with fixtures in `tests/fixtures/`
- **TypeScript**: Vitest
- **Golden tests**: Reference data in `tests/golden/`
- **Determinism tests**: Verify same inputs → same outputs

### What NOT to Do

❌ **Don't** add randomness without fixed seeds
❌ **Don't** skip provenance tracking
❌ **Don't** mutate canonical data structures
❌ **Don't** access Shadow Structural Metrics directly
❌ **Don't** push to main/master without PR
❌ **Don't** over-engineer solutions
❌ **Don't** add features beyond what was requested

---

## 🎓 Learning Path for New AI Assistants

If you're new to this repo, follow this path:

1. **Read `README.md`** (10 min) — Understand what Abraxas is
2. **Read this guide** (5 min) — Get oriented
3. **Read `CLAUDE.md`** (30 min) — Deep dive into conventions
4. **Read `docs/canon/ABRAXAS_CANON_LEDGER.txt`** (15 min) — Understand principles
5. **Explore one module** (20 min) — Pick `abraxas/lexicon/` or `abraxas/oracle/`
6. **Run tests** (10 min) — See how the system works

Total: ~90 minutes to become proficient

---

## 🔗 External References

- **Decodo API**: Web scraping integration for data ingestion
- **Drizzle ORM**: Database ORM for TypeScript
- **Pydantic**: Python data validation library
- **Zod**: TypeScript schema validation library
- **Vitest**: TypeScript testing framework

---

## 🆘 Quick Help

### "I need to understand what this module does"

1. Check `CLAUDE.md` module organization section
2. Look for `README.md` in the module directory
3. Read module `__init__.py` docstring
4. Check tests in `tests/test_<module>.py`

### "I need to add a new feature"

1. Check if similar feature exists (search codebase)
2. Read relevant specs in `docs/specs/`
3. Follow conventions in `CLAUDE.md`
4. Add tests BEFORE implementation (TDD)
5. Include provenance tracking
6. Verify determinism

### "I need to fix a bug"

1. Write a failing test first
2. Find root cause (don't guess)
3. Fix with minimal changes
4. Verify test passes
5. Check for side effects

### "I need to understand the architecture"

1. Read `README.md` architecture section
2. Read `CLAUDE.md` architecture section
3. Look at diagram in `README.md`
4. Trace a request through the stack:
   - HTTP request → `server/routes.ts`
   - Route calls Python CLI → `abraxas/cli/`
   - CLI uses operators → `abraxas/operators/`
   - Operators use core utilities → `abraxas/core/`

---

## 📝 Quick Reference Card

| Task | Command |
|------|---------|
| **Run tests** | `pytest tests/` or `npm test` |
| **Type check** | `npm run check` or `mypy abraxas/` |
| **System diagnostic** | `abx doctor` |
| **Start dev server** | `npm run dev` |
| **Build for production** | `npm run build` |
| **Run SCO analysis** | `python -m abraxas.cli.sco_run --records data.json --out events.jsonl` |
| **Start UI server** | `abx ui` |
| **Find files** | `find . -name "*.py" | grep oracle` |
| **Search code** | `grep -r "pattern" abraxas/` |
| **Git status** | `git status` |
| **Create PR** | `gh pr create --title "Title" --body "Body"` |

---

## 🎯 Key Takeaways

1. **Determinism is non-negotiable** — Same inputs ALWAYS produce same outputs
2. **Provenance everywhere** — SHA-256 hashes for all transformations
3. **CLAUDE.md is your bible** — Read it thoroughly
4. **Tests are mandatory** — No feature without tests
5. **Shadow Structural Metrics are locked** — Access via ϟ₇ only
6. **ABX-Runes are powerful** — Learn the symbolic operator system
7. **Avoid over-engineering** — Keep solutions simple and focused

---

## 📞 Getting Help

- **Documentation**: Check `docs/` directory first
- **Code examples**: Look in `examples/` and `tests/`
- **Specifications**: Check `docs/specs/` for technical details
- **Canonical principles**: Read `docs/canon/ABRAXAS_CANON_LEDGER.txt`

---

**Last Updated**: 2025-12-29
**Version**: 1.0.0
**Maintained by**: Abraxas development team

---

**Welcome to Abraxas!** 🜏

You're now ready to work with this repository. Remember: **determinism, provenance, and simplicity** are the core values. When in doubt, check `CLAUDE.md` or the relevant specification documents.

Happy coding! 🚀
