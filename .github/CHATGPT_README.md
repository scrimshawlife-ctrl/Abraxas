# ChatGPT Quick Access Guide for Abraxas

**This file is specifically designed for ChatGPT when accessing the repository via GitHub integration.**

---

## 🎯 Start Here

**Abraxas** = Weather system for language. Detects linguistic compression (eggcorns), tracks memetic drift, runs as edge appliance.

**Your first 3 actions**:
1. Read this file (you're here)
2. Read [AI_ASSISTANT_GUIDE.md](AI_ASSISTANT_GUIDE.md) — Comprehensive guide
3. Read [../CLAUDE.md](../CLAUDE.md) — Development conventions

---

## 📚 Documentation Hierarchy

**Start here** → **Then check** → **Deep dive**

1. **This file** → Quick ChatGPT-specific orientation
2. **[AI_ASSISTANT_GUIDE.md](AI_ASSISTANT_GUIDE.md)** → Full AI assistant guide (15 min read)
3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** → Ultra-condensed cheat sheet (2 min read)
4. **[../README.md](../README.md)** → Project overview, features, architecture
5. **[../CLAUDE.md](../CLAUDE.md)** → Comprehensive development guide (30 min read)
6. **[../docs/canon/ABRAXAS_CANON_LEDGER.txt](../docs/canon/ABRAXAS_CANON_LEDGER.txt)** — Design principles

---

## 🏗️ Repository Map

```
Abraxas/
├── .github/                    # YOU ARE HERE
│   ├── CHATGPT_README.md       # This file
│   ├── AI_ASSISTANT_GUIDE.md   # Full AI guide
│   └── QUICK_REFERENCE.md      # Cheat sheet
│
├── abraxas/                    # Python core
│   ├── core/                   # Provenance, metrics, tau
│   ├── operators/              # SCO/ECO operators
│   ├── linguistic/             # Phonetics, similarity
│   ├── shadow_metrics/         # LOCKED (access via ϟ₇ only)
│   └── runes/                  # ABX-Runes operators
│
├── server/                     # TypeScript Express API
├── client/                     # React frontend
├── tests/                      # pytest tests
├── docs/                       # Specs and documentation
│
├── README.md                   # Project overview
└── CLAUDE.md                   # Development guide (ESSENTIAL)
```

---

## ⚡ Critical Rules (Must Follow)

### 1. Determinism is Mandatory
**Same inputs → same outputs (ALWAYS)**
- No `random()` without fixed seeds
- Stable sorting with explicit keys
- Timestamps in ISO8601 with 'Z'

### 2. Provenance is Everywhere
**Every artifact has SHA-256 hash**
```python
from abraxas.core.provenance import Provenance, hash_canonical_json

prov = Provenance(
    run_id="RUN-001",
    started_at_utc=Provenance.now_iso_z(),
    inputs_hash=hash_canonical_json(inputs),
    config_hash=hash_canonical_json(config)
)
```

### 3. Shadow Structural Metrics are LOCKED
**Access ONLY via ABX-Runes ϟ₇**
```python
# ✅ CORRECT
from abraxas.runes.operators.sso import apply_sso
result = apply_sso({"symbol_pool": [...]})

# ❌ WRONG (raises AccessDeniedError)
from abraxas.shadow_metrics import compute_sei
```

### 4. Write-Once, Annotate-Only
**Canonical data is immutable**
- Never mutate existing canonical entries
- Add annotations instead (append-only)

---

## 🔑 Key Concepts

| Concept | What It Is | Where to Learn |
|---------|-----------|----------------|
| **SCO/ECO** | Symbolic compression detection | `README.md`, `abraxas/operators/` |
| **STI** | Symbolic Transparency Index | `abraxas/linguistic/transparency.py` |
| **RDV** | Replacement Direction Vector | `abraxas/linguistic/rdv.py` |
| **τ (Tau)** | Temporal metrics (half-life, velocity, phase) | `abraxas/core/temporal_tau.py` |
| **SSM** | Shadow Structural Metrics (SEI/CLIP/NOR/PTS/SCG/FVC) | `docs/specs/shadow_structural_metrics.md` |
| **ABX-Runes** | Symbolic operators (ϟ₁-ϟ₇) | `abraxas/runes/` |
| **SEED** | Provenance framework | `CLAUDE.md` |

---

## 🎓 Learning Path (90 min)

1. **Read this file** (5 min) ✅ You're here
2. **Skim [README.md](../README.md)** (10 min) — Get overview
3. **Read [AI_ASSISTANT_GUIDE.md](AI_ASSISTANT_GUIDE.md)** (20 min) — Full guide
4. **Read [../CLAUDE.md](../CLAUDE.md)** (30 min) — Deep dive conventions
5. **Read [../docs/canon/ABRAXAS_CANON_LEDGER.txt](../docs/canon/ABRAXAS_CANON_LEDGER.txt)** (15 min) — Principles
6. **Explore one module** (10 min) — Pick `abraxas/lexicon/` or `abraxas/oracle/`

---

## 🛠️ Common Tasks

### Task: Help user understand a module
1. Check `CLAUDE.md` module organization section
2. Read module's `README.md` (if exists)
3. Read module `__init__.py` docstring
4. Look at tests in `tests/test_<module>.py`
5. Summarize for user

### Task: Help user add a feature
1. Check if similar feature exists (search codebase)
2. Find relevant spec in `docs/specs/`
3. Review conventions in `CLAUDE.md`
4. Suggest implementation following determinism/provenance rules
5. Remind about tests

### Task: Help user debug an issue
1. Ask for error message and context
2. Find relevant code (use file structure above)
3. Check tests for examples
4. Suggest fix following conventions
5. Verify determinism preserved

---

## 📋 Quick Command Reference

```bash
# Testing
pytest tests/                   # Python tests
npm test                        # TypeScript tests
abx smoke                       # Quick smoke test

# Development
npm run dev                     # Start dev server
abx doctor                      # System diagnostic
abx ui                          # UI server

# Code Search
grep -r "pattern" abraxas/      # Search Python code
find . -name "*.py"             # Find Python files

# Git
git status                      # Check status
git push -u origin <branch>     # Push (retry on fail: 2s, 4s, 8s, 16s)
gh pr create                    # Create PR
```

---

## 🚨 Common Pitfalls to Avoid

❌ **Don't** add randomness without seeds
❌ **Don't** skip provenance tracking
❌ **Don't** mutate canonical data
❌ **Don't** access Shadow Metrics directly (use ϟ₇)
❌ **Don't** over-engineer solutions
❌ **Don't** push to main/master without PR
❌ **Don't** assume — verify determinism

---

## 💡 Pro Tips for ChatGPT

### When Suggesting Code
1. **Always include provenance** for transformations
2. **Verify determinism** — same inputs → same outputs
3. **Add type hints** (Python) or types (TypeScript)
4. **Follow naming conventions** (`snake_case` for Python, `camelCase` for TS)
5. **Include tests** in your suggestions

### When Explaining Code
1. **Mention provenance** if present
2. **Highlight determinism** guarantees
3. **Reference canonical docs** (link to specs)
4. **Explain trade-offs** clearly
5. **Keep it simple** — avoid jargon unless necessary

### When Debugging
1. **Check for randomness** first
2. **Verify provenance chain** is intact
3. **Look at tests** for expected behavior
4. **Consider determinism** impact
5. **Suggest minimal changes**

---

## 🔗 Most Important Links

| Link | Purpose | Priority |
|------|---------|----------|
| [AI_ASSISTANT_GUIDE.md](AI_ASSISTANT_GUIDE.md) | Full guide for AI assistants | **HIGH** |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Cheat sheet | **HIGH** |
| [../CLAUDE.md](../CLAUDE.md) | Development conventions | **CRITICAL** |
| [../README.md](../README.md) | Project overview | **MEDIUM** |
| [../docs/specs/](../docs/specs/) | Technical specs | **MEDIUM** |
| [../docs/canon/ABRAXAS_CANON_LEDGER.txt](../docs/canon/ABRAXAS_CANON_LEDGER.txt) | Design principles | **HIGH** |

---

## 🎯 Your Action Plan

**Right now**:
1. ✅ You read this file
2. → Read [AI_ASSISTANT_GUIDE.md](AI_ASSISTANT_GUIDE.md) (20 min)
3. → Skim [../CLAUDE.md](../CLAUDE.md) (focus on Module Organization section)

**When user asks for help**:
1. Check relevant module in `abraxas/` or `server/`
2. Look at tests in `tests/`
3. Reference conventions in `CLAUDE.md`
4. Provide answer with provenance/determinism in mind

**When stuck**:
1. Search for similar code: `grep -r "similar_pattern" .`
2. Check specs: `docs/specs/`
3. Look at test examples: `tests/`
4. Remind user about `CLAUDE.md`

---

## 📞 Need More Help?

- **Full AI guide**: [AI_ASSISTANT_GUIDE.md](AI_ASSISTANT_GUIDE.md)
- **Quick reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Development guide**: [../CLAUDE.md](../CLAUDE.md)
- **Specifications**: [../docs/specs/](../docs/specs/)
- **Examples**: [../examples/](../examples/)

---

**Version**: 1.0.0
**Last Updated**: 2025-12-29
**Optimized for**: ChatGPT with GitHub integration

---

**Welcome to Abraxas!** 🜏

You're now equipped to help users with this repository. Remember the three core principles:

1. **Determinism** — Same inputs → same outputs
2. **Provenance** — SHA-256 everything
3. **Simplicity** — No over-engineering

When in doubt, check `CLAUDE.md` or suggest the user read relevant specs.

Happy assisting! 🚀
