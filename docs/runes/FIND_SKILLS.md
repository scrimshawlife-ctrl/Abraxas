# RUNE.FIND_SKILLS

## Purpose
Deterministic discovery-only lookup over registered skill sources. Ranks only registered entries and returns provenance-linked matches.

## Authority Boundaries
- Status: Canon-Shadow
- Authority: `discovery_only`
- Runtime defaults to `NOT_COMPUTABLE` when required evidence/sources are unavailable.
- No inference of unregistered skills.
- No execution/promotion/fabrication of discovered skills.

## Input Schema
- `schemas/FindSkillsInput.v1.json`
- Fields:
  - `query` (string)
  - `domains` (string[])
  - `capabilities` (string[])
  - `limit` (integer)
  - `include_shadow` (boolean)
  - `sources` (string[])

## Output Schema
- `schemas/FindSkillsOutput.v1.json`
- Fields:
  - `status` (`OK | NOT_COMPUTABLE`)
  - `matches[]` with `skill_id`, `name`, `description`, `domains`, `capabilities`, `confidence`, `source`, `provenance`
  - `total`
  - `query_hash`
  - `shadow_summary`

## Source Rules
Primary source:
- `aal_core/runes/catalog.v0.yaml`

Secondary sources are accepted only if already registered; current implementation fails closed for unregistered sources.

## Failure Rules (`NOT_COMPUTABLE`)
- Registry unavailable
- Empty query
- Source payload malformed
- Input/output schema validation failure
- Unregistered source requested

## Scoring
Deterministic weighted score:

```
score =
  name_match        * 0.40 +
  capability_match  * 0.30 +
  domain_match      * 0.20 +
  description_match * 0.10
```

- Threshold: `0.30`
- Sort: score descending, tie-break by `skill_id` ascending
- Limit applied after sorting

## Provenance
- Query hash:
  `sha256(normalized_query + normalized_domains + normalized_capabilities + limit + source_set)`
- Match hash:
  `sha256(skill_id + version + registry_path)`

## Shadow Diagnostics
Detect-only diagnostics:
- duplicate `skill_id`
- missing metadata (`name`, `description`, `domains`, `capabilities`)
- same `name` with divergent capability sets
- orphaned files in `/skills` not represented in registry
- schema references that do not exist

Diagnostics do not modify ranking, except hard fail conditions above.

## Tests
- deterministic replay (same input -> identical output)
- missing registry -> `NOT_COMPUTABLE`
- empty query -> `NOT_COMPUTABLE`
- ranking stability + tie-break stability
- hash consistency
- duplicate-skill detection
- missing-metadata detection
- schema existence validation
- 12-run invariance

## Example Output
```json
{
  "status": "OK",
  "matches": [
    {
      "skill_id": "RUNE.FIND_SKILLS",
      "name": "Find Skills",
      "description": "Deterministic skill discovery",
      "domains": ["discovery"],
      "capabilities": ["find", "registry"],
      "confidence": 1.0,
      "source": "aal_core/runes/catalog.v0.yaml",
      "provenance": {
        "registry_path": "aal_core/runes/catalog.v0.yaml",
        "hash": "<sha256>"
      }
    }
  ],
  "total": 1,
  "query_hash": "<sha256>",
  "shadow_summary": {
    "duplicate_skill_ids": [],
    "missing_metadata": [],
    "capability_drift_flags": []
  }
}
```
