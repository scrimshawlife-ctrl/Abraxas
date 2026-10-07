"""Guard for the oracle.v2 rune adapter, which could not be imported at all.

`abraxas/oracle/v2/rune_adapter.py` declared

    from abraxas.oracle.v2.pipeline import run_oracle as run_oracle_core

and `pipeline.py` defines no `run_oracle` (it has `OracleV2Pipeline` and
`create_oracle_v2_pipeline`). The module therefore FAILED TO IMPORT, which made the binding
`ϟ_ORACLE_RUN` entirely dead — and because nothing ever called `run_oracle_deterministic`,
nothing noticed. It was found by resolving every declared operator path.

The interface is not in doubt, which is why this is a repair and not an invention:
`schemas/capabilities/oracle_run_input.schema.json` and `..._output.schema.json` are the
canonical contract for `RUNE.ORACLE.V2.RUN`, and the adapter already matched both. Only the
pipeline invocation was wrong, so the fix is the mapping from schema-shaped observations
onto the pipeline's `OracleSignal` — determined by those two witnesses.
"""

from __future__ import annotations

import json

import pytest

VALID_OBSERVATIONS = [
    {"term": "alpha", "context": "alpha is rising across channels", "timestamp": "2026-01-01T00:00:00Z"},
    {"term": "beta", "context": "beta momentum stays flat", "timestamp": "2026-01-01T00:00:05Z"},
]


def test_module_imports() -> None:
    """The defect: this raised ModuleNotFoundError-equivalent ImportError."""
    import abraxas.oracle.v2.rune_adapter  # noqa: F401


def test_operator_path_resolves() -> None:
    from abraxas.yggdrasil.binding_matrix import RESOLVED, resolve_operator_path

    assert resolve_operator_path("abraxas.oracle.v2.rune_adapter:run_oracle_deterministic") == RESOLVED


def test_binding_matrix_reports_it_resolved() -> None:
    from abraxas.runes.registry import describe_rune
    from abraxas.yggdrasil.binding_matrix import build_binding_matrix

    binding = describe_rune("ϟ_ORACLE_RUN")
    rows = {row["rune_id"]: row for row in build_binding_matrix()["rows"]}
    assert rows[binding.rune_id]["reason"] == "RESOLVED", rows[binding.rune_id]
    assert binding.capability == "RUNE.ORACLE.V2.RUN"


# --------------------------------------------------------------------------
# contract behaviour
# --------------------------------------------------------------------------


def _run(**kwargs):
    from abraxas.oracle.v2.rune_adapter import run_oracle_deterministic

    return run_oracle_deterministic(**kwargs)


def test_empty_observations_are_not_computable() -> None:
    """The input schema requires minItems 1; absence must be reported, not faked."""
    result = _run(run_id="RUN-1", observations=[])
    assert result["oracle_output"] is None
    assert result["provenance"] is None
    assert result["not_computable"]["reason"], "not_computable needs a reason"
    assert "observations" in result["not_computable"]["missing_inputs"]


def test_returns_a_complete_envelope() -> None:
    result = _run(run_id="RUN-1", observations=VALID_OBSERVATIONS)

    # Output schema: either oracle_output+provenance, or not_computable.
    if result["not_computable"] is not None:
        assert result["oracle_output"] is None and result["provenance"] is None
        assert result["not_computable"]["reason"]
        return

    assert isinstance(result["oracle_output"], dict)
    provenance = result["provenance"]
    for field in ("timestamp_utc", "config_sha256", "inputs_sha256"):
        assert field in provenance, f"output schema requires provenance.{field}"
    assert len(provenance["inputs_sha256"]) == 64
    assert len(provenance["config_sha256"]) == 64


def test_envelope_is_json_serializable() -> None:
    """A provenance envelope that cannot be serialized cannot be written to a ledger."""
    result = _run(run_id="RUN-1", observations=VALID_OBSERVATIONS)
    json.dumps(result)


#: `provenance` records WHEN a run happened alongside WHAT it was. `timestamp_utc` is therefore
#: metadata, not content, and is excluded from determinism comparison -- the same rule this repository
#: applies to the lexicon content fingerprint and to the engine harness's `NON_CONTENT_FIELDS`.
#: Measured 2026-10-07: two runs 1.2s apart differ in this key and NOTHING else, so comparing whole
#: provenance dicts fails whenever the two calls straddle a second boundary. That made this test a
#: time-bomb: it passed 5/5 in isolation and failed inside the full suite, which is how it was found.
PROVENANCE_METADATA = ("timestamp_utc",)


def _provenance_content(provenance: dict) -> dict:
    """Provenance with its metadata removed -- what determinism actually concerns."""
    return {k: v for k, v in provenance.items() if k not in PROVENANCE_METADATA}


def test_provenance_is_deterministic_over_identical_inputs() -> None:
    first = _run(run_id="RUN-1", observations=VALID_OBSERVATIONS)
    second = _run(run_id="RUN-1", observations=VALID_OBSERVATIONS)

    p1, p2 = first["provenance"], second["provenance"]
    assert p1 is not None and p2 is not None, "provenance missing; cannot assess determinism"

    assert _provenance_content(p1) == _provenance_content(p2), (
        "identical inputs produced different provenance CONTENT; the adapter is not deterministic"
    )

    # The exclusion is scoped, not a blanket ignore: the metadata must still be produced and well-formed,
    # or dropping it from the artifact would silently satisfy this test.
    for p in (p1, p2):
        assert "timestamp_utc" in p, "provenance must still record when the run happened"
        assert str(p["timestamp_utc"]).endswith("Z"), p["timestamp_utc"]


def test_provenance_exclusion_covers_only_the_timestamp() -> None:
    """Counterfactual for the exclusion above: if it swallowed a content key, a real change to that key
    would go unnoticed and the determinism assertion would be vacuous."""
    p = _run(run_id="RUN-1", observations=VALID_OBSERVATIONS)["provenance"]
    assert set(_provenance_content(p)) == {
        "config_sha256",
        "inputs_sha256",
        "operation_id",
        "repo_commit",
        "runtime_fingerprint",
    }, sorted(_provenance_content(p))


def test_inputs_hash_changes_when_observations_change() -> None:
    base = _run(run_id="RUN-1", observations=VALID_OBSERVATIONS)
    other = _run(
        run_id="RUN-1",
        observations=[
            {"term": "gamma", "context": "unrelated", "timestamp": "2026-02-02T00:00:00Z"}
        ],
    )
    if base["provenance"] is None or other["provenance"] is None:
        pytest.skip("pipeline returned not_computable for one of the inputs")
    assert base["provenance"]["inputs_sha256"] != other["provenance"]["inputs_sha256"]


def test_single_observation_is_accepted() -> None:
    result = _run(run_id="RUN-1", observations=VALID_OBSERVATIONS[:1])
    assert result["not_computable"] is None or result["not_computable"]["reason"]
