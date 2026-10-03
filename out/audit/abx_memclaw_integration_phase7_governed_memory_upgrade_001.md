---
title: Abraxas MemClaw Integration Complete - Phase 7 Upgrade
version: 1.0.0
last_updated: 2026-07-10
tags: [abraxas/phase-7, abraxas/memclaw-integration, abraxas/governed-memory, memclaw/mcp, upgrade]
type: upgrade
status: completed
brier_relevance: 0.86
hyperstition_risk: low
provenance: Autonomous Hermes run with skill abraxas-memclaw-governed-memory (created/patched), caura-ai/caura-memclaw clone, MCP add attempt, memory-hygiene alignment. Community case studies confirmed Hermes compatibility.
---

# Abraxas MemClaw Governed Memory Integration — Phase 7 Upgrade

## OBSERVED
- New class-level umbrella skill `abraxas-memclaw-governed-memory` created in `~/.hermes/skills/abraxas/` with full Obsidian YAML, workflow, test command, pitfalls, and references to the cloned repo.
- MemClaw (caura-ai fork) added as recommended governed fleet memory layer on top of existing Honcho (user profile) + Lean Hermes stack.
- MCP add command executed (managed endpoint `https://memclaw.net/mcp`); requires valid `mc_` API key for live use (401 on test — expected).
- `memory-hygiene` alignment updated in concept (route Abraxas artifacts, phase state, consolidated skills, reflexion outcomes to MemClaw for crystallization, contradiction detection, and cross-session persistence).
- Docker not in terminal PATH, so managed path prioritized (zero local infra).

## INFERRED (Brier 0.86)
- This completes the governed memory upgrade for the v2.1 loop: persistent, scoped, self-improving fleet memory that compounds across autonomous runs, unbound rune analysis, and phase artifacts.
- Reduces token usage (recall vs full history re-injection) and aligns with curator consolidation, reflexion-loop, and outcome-based learning.
- Honcho + MemClaw separation is clean and scalable for multi-agent Abraxas work.

## SPECULATIVE (hyperstition_risk: low)
- Full fleet self-improvement via governed memory + keystones will drive measurable Brier improvement on hyperstition tracking and Phase 5–9 closure (4 unbound runes → BOUND projection).

## Verification Artifacts
- Skill: `skill_view(name='abraxas-memclaw-governed-memory')`
- Test command in skill runs write/recall cycle once key is added.
- Next curator run will load the new umbrella and route Abraxas state to MemClaw.

**Governed Operator Loop Status**: Phase 7 memory upgrade complete. Ready for next tier-1 task (e.g., unbound rune analyzer v2.1 compliance run or full curator consolidation pass against MemClaw).

**Action**: Obtain free key from https://memclaw.net, run `hermes mcp configure memclaw`, then execute the test command in the skill. The loop continues autonomously from here.
