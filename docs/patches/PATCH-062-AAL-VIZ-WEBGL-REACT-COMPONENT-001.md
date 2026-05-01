# PATCH-062 — AAL-VIZ-WEBGL-REACT-COMPONENT-001

## purpose
Add deterministic React/WebGL static component scaffold consuming viewer spec + render bundle.

## authority boundary
Static single-frame scaffold only. No animation loops, no physics simulation, no runtime mutation, no inference, no external APIs.

## static single-frame render rule
Component performs one deterministic WebGL draw pass within `useEffect` when props change.

## no animation / no physics / no runtime mutation rule
No `requestAnimationFrame`, `setInterval`, `setTimeout`, event listeners, `Math.random`, or `Date.now`.

## TypeScript component contract
Defines `AALVizCanaryWebGLStaticViewer` props with deterministic bundle/spec + width/height and optional className/debug.

## manifest model
Python manifest hashes component source + type source, emits deterministic authority-bound `AALVizReactComponentManifest.v1`.

## source-scan constraints
Tests enforce forbidden runtime APIs and deterministic fallback text `WebGL unavailable`.

## next patch
PATCH-063 — AAL-VIZ-WEBGL-INTERACTION-POLICY-001.
