# abx-familiar v0.1.x — CANARY Pack

## Purpose
Provide a minimal invariance harness and CI hook to detect deterministic drift.

## What Runs in CI
- pytest unit tests
- CANARY invariance harness (pure mode, no ledger)

## Non-Goals
- No ERS scheduling
- No adapters for web/file/sensor
- No semantic inference
- No promotion beyond SHADOW

## Pass/Fail
- CI fails if CANARY runner reports hash mismatch across runs.
