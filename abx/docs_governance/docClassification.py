from __future__ import annotations

from abx.docs_governance.docInventory import build_doc_inventory


DOC_CLASSES = (
    "authoritative_reference",
    "generated_summary",
    "operator_guide",
    "maintainer_guide",
    "onboarding_surface",
    "legacy_redundant_candidate",
)


def classify_doc_surfaces() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in DOC_CLASSES}
    for row in build_doc_inventory():
        out[row.doc_class].append(row.doc_id)
    return {k: sorted(v) for k, v in out.items()}


def detect_duplicate_doc_surfaces() -> list[str]:
    seen: set[tuple[str, str]] = set()
    dup: list[str] = []
    for row in build_doc_inventory():
        key = (row.path, row.doc_class)
        if key in seen:
            dup.append(row.doc_id)
            continue
        seen.add(key)
    return sorted(dup)
