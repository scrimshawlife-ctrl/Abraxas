from __future__ import annotations

from abx.docs_governance.docInventory import build_doc_inventory


def build_doc_ownership() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in build_doc_inventory():
        out.setdefault(row.ownership, []).append(row.doc_id)
    return {k: sorted(v) for k, v in sorted(out.items())}
