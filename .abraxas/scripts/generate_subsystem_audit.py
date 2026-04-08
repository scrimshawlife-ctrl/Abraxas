#!/usr/bin/env python3
import json
from _common import parser_base, load_subsystem

def main()->int:
    p=parser_base("Generate subsystem audit")
    p.add_argument("--subsystem", required=True)
    a=p.parse_args()
    s=load_subsystem(a.subsystem)
    report={"subsystem_id":a.subsystem,"release_readiness":s["release_readiness"],"required_receipts":s["required_receipts"],"promotion_state":s["promotion_state"]}
    print(json.dumps(report,indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
