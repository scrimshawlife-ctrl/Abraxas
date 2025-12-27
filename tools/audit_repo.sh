#!/usr/bin/env bash
set -euo pipefail
python3 tools/audit_repo.py
cat data/audit_report.json | python3 -m json.tool >/dev/null
echo "OK: data/audit_report.json"
