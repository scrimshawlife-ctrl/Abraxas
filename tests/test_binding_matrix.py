"""Guard for the rune→YGGDRASIL binding matrix.

`abraxas/runes/registry.py` declares an `operator_path` for every binding and never checked
that it resolves. `load_registry` will synthesise a default path for any rune, so the
registry could claim an operator for a rune that has none and nothing could tell the
difference. The matrix resolves each claim and records an explicit reason.

These tests hold two things: that the reasons are honest (closed set, consistent with
`resolved`), and that the count of unusable bindings can only go DOWN.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from abraxas.yggdrasil.binding_matrix import (
    BINDING_REASONS,
    IMPORT_FAILED,
    MALFORMED_OPERATOR_PATH,
    MISSING_OPERATOR,
    NOT_CALLABLE,
    NO_OPERATOR_DECLARED,
    RESOLVED,
    build_binding_matrix,
    resolve_operator_path,
    unresolved_rows,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "contracts" / "yggdrasil" / "rune_route_binding_matrix.v1.schema.json"

#: Ratchet. Was 7 before the stale forecast operator name was corrected to
#: `record_forecast_outcome_deterministic`, then 6 before `ϟ_ORACLE_RUN` was repaired.
#: This number may only ever DECREASE — lower it in the same commit that fixes a binding,
#: and never raise it without saying why in the commit body. Same idiom as
#: tests/test_coupling_lint.py (MAX_ALLOWED_VIOLATIONS).
MAX_UNRESOLVED_BINDINGS = 5

#: Bindings known to be unusable, pinned so that fixing one is a conscious edit here too.
#: Reported, not hidden: each needs a different fix, which is why the reasons differ.
KNOWN_UNUSABLE = {
    # module imports, but names no such symbol. The builders live in their own modules
    # (e.g. abraxas/evolve/epp_builder.py:build_epp); these adapter functions were never
    # written.
    "ϟ_EVOLVE_CANON_DIFF_BUILD": MISSING_OPERATOR,
    "ϟ_EVOLVE_EPP_BUILD": MISSING_OPERATOR,
    "ϟ_EVOLVE_EVOGATE_BUILD": MISSING_OPERATOR,
    "ϟ_EVOLVE_PROMOTION_BUILD": MISSING_OPERATOR,
    "ϟ_EVOLVE_RIM_BUILD": MISSING_OPERATOR,
}


@pytest.fixture(scope="module")
def matrix() -> dict:
    return build_binding_matrix()


# --------------------------------------------------------------------------
# resolve_operator_path: every reason is reachable and correct
# --------------------------------------------------------------------------


def test_resolves_a_real_callable() -> None:
    assert resolve_operator_path("json:dumps") == RESOLVED


def test_empty_path_is_no_operator_declared() -> None:
    assert resolve_operator_path("") == NO_OPERATOR_DECLARED


@pytest.mark.parametrize("path", ["json", "json:", ":dumps", "no-colon-here"])
def test_malformed_paths_are_reported(path: str) -> None:
    assert resolve_operator_path(path) == MALFORMED_OPERATOR_PATH


def test_unimportable_module_is_import_failed_not_missing_operator() -> None:
    """The distinction matters: a broken module and a wrong symbol need different fixes."""
    assert resolve_operator_path("definitely.not.a.module:thing") == IMPORT_FAILED


def test_importable_module_without_the_attribute_is_missing_operator() -> None:
    assert resolve_operator_path("json:no_such_attribute") == MISSING_OPERATOR


def test_non_callable_attribute_is_not_callable() -> None:
    assert resolve_operator_path("json:__doc__") == NOT_CALLABLE


# --------------------------------------------------------------------------
# matrix shape: the contract
# --------------------------------------------------------------------------


def test_schema_file_exists_and_declares_the_version(matrix) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["properties"]["schema_version"]["const"] == matrix["schema_version"]


def test_matrix_carries_exactly_the_contract_keys(matrix) -> None:
    assert set(matrix) == {
        "schema_version",
        "total",
        "resolved",
        "unresolved",
        "by_reason",
        "duplicate_rune_ids",
        "rows",
    }


def test_counts_are_internally_consistent(matrix) -> None:
    assert matrix["total"] == len(matrix["rows"])
    assert matrix["total"] == matrix["resolved"] + matrix["unresolved"]
    assert sum(matrix["by_reason"].values()) == matrix["total"]
    assert matrix["by_reason"][RESOLVED] == matrix["resolved"]


def test_by_reason_always_carries_every_reason(matrix) -> None:
    """Present at zero, so a consumer can rely on the key set across runs."""
    assert set(matrix["by_reason"]) == set(BINDING_REASONS)


def test_every_row_reason_is_in_the_closed_set(matrix) -> None:
    unknown = sorted({row["reason"] for row in matrix["rows"]} - set(BINDING_REASONS))
    assert unknown == [], f"free-text reasons are not allowed: {unknown}"


def test_resolved_flag_agrees_with_the_reason(matrix) -> None:
    for row in matrix["rows"]:
        assert row["resolved"] is (row["reason"] == RESOLVED), row


def test_resolved_rows_declare_a_module_attribute_path(matrix) -> None:
    for row in matrix["rows"]:
        if row["resolved"]:
            module_path, sep, attribute = row["operator_path"].partition(":")
            assert sep and module_path and attribute, row


def test_no_duplicate_rune_ids(matrix) -> None:
    """A duplicated id means two bindings answer to one name."""
    assert matrix["duplicate_rune_ids"] == []


# --------------------------------------------------------------------------
# determinism
# --------------------------------------------------------------------------


def test_matrix_is_deterministic(matrix) -> None:
    assert build_binding_matrix() == matrix


def test_rows_are_sorted_by_rune_id(matrix) -> None:
    keys = [(row["rune_id"], row["capability"]) for row in matrix["rows"]]
    assert keys == sorted(keys)


# --------------------------------------------------------------------------
# ratchet + the known-unusable set
# --------------------------------------------------------------------------


def test_unresolved_bindings_do_not_exceed_the_ratchet(matrix) -> None:
    unresolved = unresolved_rows(matrix)
    assert len(unresolved) <= MAX_UNRESOLVED_BINDINGS, (
        f"{len(unresolved)} unusable bindings, ratchet is {MAX_UNRESOLVED_BINDINGS}.\n"
        + "\n".join(f"  {r['reason']:16} {r['rune_id']}  {r['operator_path']}" for r in unresolved)
    )


def test_known_unusable_bindings_are_exactly_as_recorded(matrix) -> None:
    """Pins the current set so fixing one is a conscious edit, and so a NEW unusable
    binding cannot appear while the total stays under the ratchet."""
    actual = {row["rune_id"]: row["reason"] for row in unresolved_rows(matrix)}
    assert actual == KNOWN_UNUSABLE, (
        "the set of unusable bindings changed.\n"
        f"  newly broken : {sorted(set(actual) - set(KNOWN_UNUSABLE))}\n"
        f"  newly fixed  : {sorted(set(KNOWN_UNUSABLE) - set(actual))}\n"
        f"  changed kind : "
        f"{sorted(k for k in set(actual) & set(KNOWN_UNUSABLE) if actual[k] != KNOWN_UNUSABLE[k])}"
    )


def test_import_failed_bindings_are_a_broken_module_not_a_typo(matrix) -> None:
    """`IMPORT_FAILED` means nothing using that binding can work at all — the loudest
    reason, so it is asserted separately rather than folded into the count.

    Zero is the correct number here: a binding that references an unimportable module is
    dead, not merely degraded. `ϟ_ORACLE_RUN` was the sole instance (its adapter imported a
    `run_oracle` that pipeline.py never defined) and has been repaired.
    """
    broken = [row["rune_id"] for row in matrix["rows"] if row["reason"] == IMPORT_FAILED]
    assert broken == [], (
        "no binding may reference a module that cannot be imported. "
        f"Found: {broken}"
    )
