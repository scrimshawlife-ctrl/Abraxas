#!/usr/bin/env python3
import json
from _common import parser_base, subsystem_ids, load_subsystem

def main()->int:
    parser_base("Governance summary").parse_args()
    rows=[]
    for sid in subsystem_ids():
        s=load_subsystem(sid)
        rows.append({"subsystem":sid,"lane":s["lane"],"promotion_state":s["promotion_state"],"release_readiness":s["release_readiness"]})
    print(json.dumps({"subsystems":rows},indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
