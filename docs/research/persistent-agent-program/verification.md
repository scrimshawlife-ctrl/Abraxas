# Candidate package verification

Date: 2026-09-14. Status: candidate; documentation and existing component checks only.

| Scope | Command/check | Result |
|---|---|---|
| Noema-Specs | python validation/validate_all.py | PASS; 444 schemas, 923 example files; existing conformance checks passed |
| Noema-Specs | python validation/validate_direction.py | PASS |
| Noesis | python scripts/validate_specs.py | PASS |
| Semion | PYTHONPATH=src python -m pytest -q | 9 passed |
| Trutina | PYTHONPATH=src python -m pytest -q | 201 passed |
| noema-client | PYTHONPATH=src python -m pytest -q tests/test_openai_adapter.py tests/test_play_bounds.py tests/test_connect_docs.py | 23 passed |
| Hyperlex | HYPERLEX_OFFLINE=1 PYTHONPATH=src:. python -m pytest -q tests/test_route_labels.py tests/shadow/test_hyperlexical_shadow.py | 26 passed |
| Program sidecar | Draft202012Validator.check_schema; validate review-only.example.json | PASS |
| Program negative schema checks | Execution authority, AVAILABLE without artifacts, OBSERVED without evidence, empty missing-evidence reason, malformed hash | All five rejected |
| Added documents | Local Markdown targets, JSON parse, requirement/workflow/acceptance/task IDs | PASS |
| Seven worktrees | git diff --check | PASS |

The workspace initially lacked jsonschema; Noema validation stopped at that missing dependency after preliminary checks. Re-ran successfully in an isolated environment with the repository requirements (jsonschema 4.26.0, PyYAML 6.0.3) and pytest 9.1.1. No validator, test expectation or dependency policy was changed to obtain success. Test-created untracked bytecode was excluded from the patch.

No full Abraxas runtime test suite, new scientific experiment, GPU invocation, training, publication, live-world action, or support application ran. AC-P01 through AC-P10 describe future end-to-end acceptance; passing these checks does not establish them. JSON Schema does not enforce artifact resolution, source rights or all cross-reference semantics; those remain explicit adoption review rules in spec.md.
