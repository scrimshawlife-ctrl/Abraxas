# PATCH-060 — AAL-VIZ-WEBGL-RENDERER-SCAFFOLD-001

## purpose
Convert `AALVizWebGLSceneSpec.v1` into a deterministic WebGL render bundle JSON scaffold.

## authority boundary
Render-bundle-only lane. No WebGL rendering, no animation runtime, no physics simulation, no browser runtime state, no mutation, and no execution loops.

## buffer mapping logic
- positions: `[x,y,0]` for each sorted node
- colors: token-mapped normalized RGB values
- indices: `[source_index,target_index]` for each sorted edge

## no-runtime rule
Outputs static draw metadata and uniforms only.

## no-render rule
Patch emits canonical JSON bundle and does not invoke any renderer.

## next patch
PATCH-061.
