from __future__ import annotations

import json

from abx.admission.admissionReports import build_change_admission_report


if __name__ == "__main__":
    print(json.dumps(build_change_admission_report(), indent=2, sort_keys=True))
