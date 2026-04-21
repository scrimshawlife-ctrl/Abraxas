# Skill Graph Projection (AAL-Viz)

## Purpose
Projection-only adapter that converts `FindSkillsOutput.v1` into a deterministic `SkillGraphProjection.v1` graph for Operator Console / AAL-Viz.

## Authority Boundary
- Non-authoritative output surface.
- `authority` is always `projection_only`.
- Projection does not alter ranking, mutate registry, execute or promote skills.

## Input
- Source payload: `FindSkillsOutput.v1` (`status` must be `OK`).
- Missing or invalid source payload returns `NOT_COMPUTABLE` from adapter.

## Output Schema
- `schemas/SkillGraphProjection.v1.json`
- Shape:
  - `projection_id`
  - `source_query_hash`
  - `nodes[]` with `{id,label,type,provenance_hash}`
  - `edges[]` with `{from,to,type}`
  - `authority: projection_only`

## Determinism Rules
- Node ordering: stable sort by `(type, id)`.
- Edge ordering: stable sort by `(type, from, to)`.
- `projection_id`: deterministic SHA-256 of canonicalized graph material.
- Nodes are generated only from source `matches[*]` domains/capabilities/skills.

## Fail-Closed Rules
Returns `NOT_COMPUTABLE` when:
- input payload missing or malformed,
- input `status != OK`,
- required skill provenance hash missing.

## Tests
- same input -> same graph
- no unregistered skill injection in projection
- skill nodes include `provenance_hash`
- stable `projection_id`
- no upstream mutation
- missing source -> `NOT_COMPUTABLE`
- stable ordering
