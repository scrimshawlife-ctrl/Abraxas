# PATCH-057 — AAL-VIZ-CANARY-SVG-RENDERER-001

## purpose
Render `AALVizCanaryGovernanceViewPacket.v1` into deterministic SVG plus deterministic render manifest JSON.

## authority boundary
Rendering-only lane. No inference, mutation, activation, promotion, scheduling, runtime config writes, external API calls, randomness, UUIDs, or wall-clock time.

## rendering model
- Input: `AALVizCanaryGovernanceViewPacket.v1`
- Output A: SVG canvas (1200x800, background `#020617`)
- Output B: `AALVizCanarySVGRenderManifest.v1`

## deterministic layout rules
- Node coordinates map from normalized coordinates using fixed transform.
- Nodes, edges, alerts, actions render in stable packet order.
- IDs are deterministic (`node-{node_id}`, `edge-{source}-{target}-{edge_type}`).
- Stable line ordering and attribute ordering are enforced by static string templates.
- Text is escaped via `html.escape`.

## color token map
- Nodes: cyan `#22d3ee`, amber `#f59e0b`, violet `#8b5cf6`, blue `#3b82f6`, green `#22c55e`, purple `#a855f7`, orange `#f97316`, default `#94a3b8`
- Alerts: critical `#ef4444`, warning `#f59e0b`, info `#22d3ee`
- Actions: high `#ef4444`, medium `#f59e0b`, low `#22d3ee`

## manifest fields
`artifact`, `schema_version`, `render_id`, `view_id`, `svg_hash`, `view_packet_hash`, `dimensions`, `counts`, `files`, `authority`.

## no inference / no mutation guarantee
Renderer computes hashes and SVG only from input packet + fixed constants. Input packet is not mutated.

## next patch
PATCH-058 — AAL-VIZ-SVG-ARTIFACT-LEDGER-001.
