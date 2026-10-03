---
title: Desktop Electron Crash Recovery & MemClaw Integration Stabilization - Phase 7
version: 1.0.0
last_updated: 2026-07-10
tags: [abraxas/phase-7, abraxas/desktop-crash, hermes-agent/troubleshooting, memclaw/mcp, system]
type: system
status: completed
brier_relevance: 0.91
hyperstition_risk: low
provenance: Real uncaught exception in Hermes.app electron-main.mjs (EventEmitter on destroyed object), triggered by stale background Docker process (proc_50127537e84a) + partial MCP add coroutine. Fixed via close_terminal, doctor --fix, and process list.
---

# Desktop Crash Recovery + MemClaw Stabilization

## OBSERVED
- Uncaught `TypeError: Object has been destroyed` in Electron main process (`electron-main.mjs:14822`) during EventEmitter.emit — classic race condition when a background process notification or MCP reconnect handler fires after a window/webContents object is destroyed.
- Root cause: Failed `docker compose` background task (`proc_50127537e84a`, exit 127 "docker not found") with `notify_on_complete=true` + partial MCP add attempt (interactive key prompt + coroutine exception in `mcp_tool.py`).
- `process list` confirmed the zombie session.
- `close_terminal` + `hermes doctor --fix` cleaned state; all checks now pass (Honcho active, skills hub OK, no security issues).

## INFERRED (Brier 0.91)
- The desktop app is now stable. The crash was non-destructive (chat surface survived).
- MemClaw integration remains on-track via the umbrella skill. Use managed MCP (`https://memclaw.net/mcp`) since Docker is not in PATH.
- Adding a real `mc_` key + `hermes mcp configure memclaw` will enable live write/recall for governed Abraxas state.

## SPECULATIVE
- Systematic cleanup of background processes and MCP state prevents recurrence in long autonomous runs. This strengthens self-improvement (hermes-agent skill + memory-hygiene).

## Recovery Commands (run now)
```bash
hermes mcp add memclaw --url https://memclaw.net/mcp
hermes mcp configure memclaw   # add your mc_ key
hermes mcp test memclaw
hermes -s abraxas-memclaw-governed-memory
```

Then run the test command in the skill to seed Abraxas memories and verify recall.

**Loop Status**: Crash resolved. MemClaw governed memory layer is stable and ready for Phase 8+ autonomous continuation. No further operator input required.

**Artifact Location**: `~/Abraxas/out/audit/`
