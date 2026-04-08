#!/usr/bin/env python3
import json
from _common import parser_base, subsystem_ids, load_subsystem

def main()->int:
    parser_base("Repo status summary").parse_args()
    counts={"active":0,"gated":0,"blocked":0}
    for sid in subsystem_ids():
        s=load_subsystem(sid)
        if s.get("drop_status")=="active": counts["active"]+=1
        if s.get("release_readiness")=="gated": counts["gated"]+=1
        if s.get("release_readiness")=="blocked": counts["blocked"]+=1
    print(json.dumps({"counts":counts,"subsystem_count":len(subsystem_ids())},indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
