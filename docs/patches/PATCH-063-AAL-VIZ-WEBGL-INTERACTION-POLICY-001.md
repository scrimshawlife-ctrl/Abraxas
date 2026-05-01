# PATCH-063 — AAL-VIZ-WEBGL-INTERACTION-POLICY-001

## purpose
Generate deterministic `AALVizWebGLInteractionPolicy.v1` from static viewer spec and react component manifest.

## authority boundary
Policy-only patch: no event binding, no runtime interaction, no animation loop, no physics simulation, no runtime mutation, no execution.

## interaction categories
Defines allowed future interaction categories and explicit forbidden runtime interactions.

## no-runtime guarantee
`event_binding_allowed=false`, `runtime_mutation_allowed=false`, and authority flags all deny runtime paths.

## state model explanation
Static interaction state progression is declared (`idle` -> `hover_candidate` -> `selected`) as metadata only.

## next patch
PATCH-064.
