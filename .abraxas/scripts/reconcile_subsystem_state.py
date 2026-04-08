#!/usr/bin/env python3
import json
from pathlib import Path
from _common import parser_base, subsystem_ids, load_subsystem

def main()->int:
    p=parser_base("Reconcile subsystem YAML and ledger")
    p.add_argument("--ledger", required=True)
    a=p.parse_args()
    seen=set()
    lp=Path(a.ledger)
    if lp.exists():
        for line in lp.read_text().splitlines():
            if line.strip():
                seen.add(json.loads(line).get("subsystem_id"))
    missing=[sid for sid in subsystem_ids() if sid not in seen]
    print(json.dumps({"missing_ledger_records":missing},indent=2))
    return 1 if missing else 0
if __name__=="__main__": raise SystemExit(main())
