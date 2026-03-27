from __future__ import annotations

import json

from abx.productization.productReports import build_product_surface_audit_report


if __name__ == "__main__":
    print(json.dumps(build_product_surface_audit_report(), indent=2, sort_keys=True))
