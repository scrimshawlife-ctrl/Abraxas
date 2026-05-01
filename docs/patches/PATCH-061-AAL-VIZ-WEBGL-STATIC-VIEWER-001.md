# PATCH-061 — AAL-VIZ-WEBGL-STATIC-VIEWER-001

## purpose
Generate deterministic `AALVizWebGLStaticViewerSpec.v1` from `AALVizWebGLRenderBundle.v1`.

## authority boundary
Static-viewer-spec-only lane; no rendering, no animation loop, no physics, no browser runtime mutation, no promotion/execution/scheduler actions.

## static viewer contract
Defines a static WebGL viewer contract with runtime mode `static_no_loop`, non-interactive policy, and deterministic draw-plan linkage.

## component contract
Declares component name, required props (`renderBundle`, `width`, `height`), and optional props (`className`, `debug`).

## props schema
Declares required/default prop semantics for static integration.

## no-loop / no-runtime / no-animation / no-physics rule
Viewer spec is metadata only; it never performs runtime operations.

## deterministic hashing rules
`render_bundle_hash` hashes canonical input bundle, `viewer_id` hashes the stable contract payload, and `viewer_spec_hash` hashes full spec excluding `viewer_spec_hash`.

## next patch
PATCH-062 — AAL-VIZ-WEBGL-REACT-COMPONENT-001.
