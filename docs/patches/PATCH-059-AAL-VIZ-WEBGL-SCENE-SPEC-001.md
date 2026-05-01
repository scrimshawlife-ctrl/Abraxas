# PATCH-059 — AAL-VIZ-WEBGL-SCENE-SPEC-001

## purpose
Generate deterministic `AALVizWebGLSceneSpec.v1` from `AALVizCanaryGovernanceViewPacket.v1`.

## authority boundary
Scene-spec-only lane: no rendering, animation runtime, physics simulation, activation, rollback, mutation, promotion, scheduling, timestamps, randomness, or UUIDs.

## deterministic layout logic
Nodes are generated in stable order and placed on a deterministic grid: `x=index%grid_width`, `y=floor(index/grid_width)`, multiplied by fixed spacing.

## no-render rule
Patch emits canonical JSON scene specification only; it does not render WebGL output.

## no-physics rule
Patch declares static animation intent and disables physics runtime authority.

## scene spec contract
Outputs artifact metadata, authority map, scene graph, camera, layout, materials, lineage hashes, and performance budget fields.

## next patch
PATCH-060.
