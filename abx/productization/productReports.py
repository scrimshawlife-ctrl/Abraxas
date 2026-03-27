from __future__ import annotations

from abx.productization.productClassification import classify_product_surfaces, detect_duplicate_product_surfaces
from abx.productization.productInventory import build_product_surface_inventory
from abx.productization.productOwnership import build_product_ownership
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_product_surface_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "ProductSurfaceAudit.v1",
        "artifactId": "product-surface-audit",
        "surfaces": [x.__dict__ for x in build_product_surface_inventory()],
        "classification": classify_product_surfaces(),
        "ownership": build_product_ownership(),
        "duplicates": detect_duplicate_product_surfaces(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
