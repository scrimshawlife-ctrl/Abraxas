"""Rune→YGGDRASIL binding matrix: resolve every declared binding, report the reason.

Why this exists
---------------
The direction of integration is rune-ward INTO the Yggdrasil plane: ABX-Runes define WHAT
may be done, YGGDRASIL defines HOW bounded capabilities connect. `abraxas/yggdrasil/registry.py`
loads all 117 bindings and registers each `rune_id`.

What was missing is that `RuneBinding.operator_path` was **declared and never resolved**.
`load_registry` will happily synthesise a default path
(``abraxas.runes.operators.<short_name>:apply_<short_name>``) for any rune, and nothing
checked that the module or attribute exists. So the registry could claim an operator for a
rune that has none, and a consumer reading the binding had no way to tell.

That is the same defect class as a manifest claiming an implementation it does not have —
and it is fixed the same way: by resolving each claim and recording an explicit reason when
it cannot be resolved, rather than assuming.

Adapted from the second attempt (``Abraxas-v2.0``,
``core/yggdrasil/rune_route_binding_matrix.py``), which classified bindings as
EXPLICIT / PARTIAL / NOT_COMPUTABLE with a stated reason. That version keyed off a *route*
concept this repo does not have, so only the part that applies is taken: **every binding
carries a reason, and an unresolvable one says so instead of looking bound.**

Output shape is frozen by
``contracts/yggdrasil/rune_route_binding_matrix.v1.schema.json``.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

#: The operator path resolves to a real attribute.
RESOLVED = "RESOLVED"
#: The module could not be imported at all — a broken module, not a wrong name.
IMPORT_FAILED = "IMPORT_FAILED"
#: The module imported but has no such attribute.
MISSING_OPERATOR = "MISSING_OPERATOR"
#: No operator path at all.
NO_OPERATOR_DECLARED = "NO_OPERATOR_DECLARED"
#: A path was declared but is not of the form ``module:attribute``.
MALFORMED_OPERATOR_PATH = "MALFORMED_OPERATOR_PATH"
#: The operator exists but is not callable.
NOT_CALLABLE = "NOT_CALLABLE"
#: Binding metadata could not be read well enough to judge it.
NOT_COMPUTABLE = "NOT_COMPUTABLE"

#: Closed set. Every row's reason must be one of these — no free-text reasons, so a
#: consumer can branch on the value without parsing prose.
#:
#: ``IMPORT_FAILED`` and ``MISSING_OPERATOR`` are deliberately separate: the first means the
#: module is broken and nothing using it can work, the second means the binding names the
#: wrong symbol. They need different fixes, so they are different reasons.
BINDING_REASONS: Tuple[str, ...] = (
    RESOLVED,
    IMPORT_FAILED,
    MISSING_OPERATOR,
    NO_OPERATOR_DECLARED,
    MALFORMED_OPERATOR_PATH,
    NOT_CALLABLE,
    NOT_COMPUTABLE,
)

SCHEMA_VERSION = "RuneRouteBindingMatrix.v1"


@dataclass(frozen=True)
class BindingRow:
    """One binding, with its resolution verdict."""

    rune_id: str
    capability: str
    operator_path: str
    reason: str

    @property
    def resolved(self) -> bool:
        return self.reason == RESOLVED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rune_id": self.rune_id,
            "capability": self.capability,
            "operator_path": self.operator_path,
            "reason": self.reason,
            "resolved": self.resolved,
        }


def resolve_operator_path(operator_path: str) -> str:
    """Return the binding reason for one operator path.

    Imports the module to check the attribute really exists. Importing is deliberate: a
    module can be present on disk and still fail to import, and a binding whose operator
    cannot be imported is not usable.
    """
    if not operator_path:
        return NO_OPERATOR_DECLARED
    if ":" not in operator_path:
        return MALFORMED_OPERATOR_PATH

    module_path, _, attribute = operator_path.partition(":")
    if not module_path or not attribute:
        return MALFORMED_OPERATOR_PATH

    try:
        module = importlib.import_module(module_path)
    except Exception:  # noqa: BLE001 - the failure IS the finding
        return IMPORT_FAILED

    if not hasattr(module, attribute):
        return MISSING_OPERATOR
    if not callable(getattr(module, attribute)):
        return NOT_CALLABLE
    return RESOLVED


def build_binding_matrix(
    bindings: Optional[Iterable[Any]] = None,
) -> Dict[str, Any]:
    """Build the matrix. Deterministic: rows are sorted by ``rune_id``.

    Pass ``bindings`` to test a specific set; the default reads the canonical registry.
    """
    if bindings is None:
        from abraxas.runes.registry import load_registry

        bindings = load_registry()

    rows: List[BindingRow] = []
    seen: Dict[str, int] = {}

    for binding in bindings:
        try:
            rune_id = str(binding.rune_id)
            capability = str(binding.capability or "")
            operator_path = str(getattr(binding, "operator_path", "") or "")
        except Exception:  # noqa: BLE001 - malformed binding is a finding, not a crash
            rows.append(
                BindingRow(
                    rune_id=repr(binding),
                    capability="",
                    operator_path="",
                    reason=NOT_COMPUTABLE,
                )
            )
            continue

        seen[rune_id] = seen.get(rune_id, 0) + 1
        rows.append(
            BindingRow(
                rune_id=rune_id,
                capability=capability,
                operator_path=operator_path,
                reason=resolve_operator_path(operator_path),
            )
        )

    rows.sort(key=lambda row: (row.rune_id, row.capability))

    by_reason: Dict[str, int] = {reason: 0 for reason in BINDING_REASONS}
    for row in rows:
        by_reason[row.reason] += 1

    duplicates = sorted(rune_id for rune_id, count in seen.items() if count > 1)

    return {
        "schema_version": SCHEMA_VERSION,
        "total": len(rows),
        "resolved": by_reason[RESOLVED],
        "unresolved": len(rows) - by_reason[RESOLVED],
        # Every reason is present even at zero, so a consumer can rely on the key set
        # without diffing across runs.
        "by_reason": by_reason,
        "duplicate_rune_ids": duplicates,
        "rows": [row.to_dict() for row in rows],
    }


def unresolved_rows(matrix: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The rows that are not usable, in matrix order."""
    return [row for row in matrix["rows"] if not row["resolved"]]


__all__ = [
    "BINDING_REASONS",
    "BindingRow",
    "IMPORT_FAILED",
    "MALFORMED_OPERATOR_PATH",
    "MISSING_OPERATOR",
    "NOT_CALLABLE",
    "NOT_COMPUTABLE",
    "NO_OPERATOR_DECLARED",
    "RESOLVED",
    "SCHEMA_VERSION",
    "build_binding_matrix",
    "resolve_operator_path",
    "unresolved_rows",
]
