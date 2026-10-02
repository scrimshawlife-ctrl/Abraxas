# Hyperlex Instrument V1 — Abraxas integration

```text
lane              = shadow
influence_policy  = NONE
valid_for_forecast = false
feature_flag      = ABX_HYPERLEX_INSTRUMENT (default off)
```

## Role

Hyperlex is a **versioned semantic instrumentation dependency**.

Abraxas consumes Hyperlex as:

```text
OBSERVATION | EVIDENCE | SHADOW_SIGNAL
```

Never as:

```text
CANONICAL_STATE | GOLD | FINAL_INTERPRETATION | AUTHORIZATION
```

```text
HYPERLEX_OUTPUT != SEMANTIC_TRUTH
```

## Flow

```text
text
  → Hyperlex Instrument observe()
  → HyperlexObservation (hyperlex.instrument.v1)
  → abraxas.evidence.hyperlex_instrument.adapt_observation
  → Abraxas advisory evidence
  → Abraxas reasoning / verification (downstream)
```

## Enable (shadow only)

```bash
export ABX_HYPERLEX_INSTRUMENT=1
export PYTHONPATH=/path/to/Hyperlex/src:$PYTHONPATH

python - <<'PY'
from abraxas.evidence.hyperlex_instrument import observe_text, assert_not_authoritative
out = observe_text("ethereum defi airdrop")
assert out["ok"]
assert_not_authoritative(out["evidence"])
print(out["evidence"]["kind"], out["evidence"]["authority"])
PY
```

Without the flag, `observe_text` returns disabled and performs no Hyperlex call.

## Adapter-only (no Hyperlex install)

```python
from abraxas.evidence.hyperlex_instrument import adapt_observation, assert_not_authoritative

evidence = adapt_observation(hyperlex_observation_dict, kind="SHADOW_SIGNAL")
assert_not_authoritative(evidence)
```

## Authority boundary

- `promote_to_canonical_state(...)` always raises.
- Non-advisory candidates are rejected at the boundary.
- `valid_for_forecast` is always false; `influence_policy` is `NONE`.

## Settlement pointer

Hyperlex classification program settlement (classifier REJECTED):

`Hyperlex/specs/007-hyperlexical-model/classification-v6-program-settlement-20261002.md`

Instrument docs: `Hyperlex/docs/instrument-v1.md`

## Subsystem

`.abraxas/subsystems/hyperlex_instrument_v1.yaml` — lane `shadow`, code authorized for additive patches only.
