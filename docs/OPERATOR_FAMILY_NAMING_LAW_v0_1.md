# Abraxas / AAL-Viz — Operator Family Naming & Entry Law v0.1

- **Status:** candidate
- **Class:** Naming Law / Authority Clarification / Operator Surface Governance
- **Purpose:** Resolve authority and navigation ambiguity across Operator Console, Operator Mode, and Operator UI by assigning one bounded role per term.

## Law

### Operator Console
Operator Console is the single canonical operator entrypoint.

- Primary read-only operator control/inspection surface
- Receives governed summaries and receipt taxonomy
- Displays execution/evidence/invariance/validator/attestation states
- Cannot mutate canon outside governed, logged actions

### Operator Mode
Operator Mode is runtime interaction state, not an authority surface.

- Examples: audit mode, investigation mode, live watch mode, stabilization mode
- Treated as mode flag/state layer only
- Never used as canonical entrypoint label

### Operator UI
Operator UI is the implementation/render shell.

- Frontend shell that may host Operator Console
- May display Operator Mode state
- Never treated as authority anchor

## Entry Rule
There is exactly one operator entrypoint in the console family:

**Operator Console**

All other surfaces must signpost role and point to the canonical entrypoint.

## Required Signage

- **Mode surfaces:** `Role: Runtime state layer / derived mode surface. Canonical entrypoint: Operator Console.`
- **UI shell surfaces:** `Role: Implementation shell / presentation layer. Canonical entrypoint: Operator Console.`
- **Build artifacts:** `Role: Build artifact / implementation surface (not a console). Canonical entrypoint: Operator Console.`

## Short Doctrine

Operator Console is the entrypoint. Operator Mode is the state. Operator UI is the shell.
