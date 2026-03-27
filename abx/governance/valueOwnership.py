from __future__ import annotations

from abx.governance.valueModel import build_value_model


def value_ownership_report() -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    for row in build_value_model():
        owners.setdefault(row.owner, []).append(row.value_id)
    return {owner: sorted(values) for owner, values in sorted(owners.items())}
