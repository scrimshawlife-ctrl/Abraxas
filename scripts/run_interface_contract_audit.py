from __future__ import annotations

import json

from abx.interface.contractReports import build_interface_contract_report


if __name__ == "__main__":
    print(json.dumps(build_interface_contract_report(), indent=2, sort_keys=True))
