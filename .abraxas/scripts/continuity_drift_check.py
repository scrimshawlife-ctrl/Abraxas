#!/usr/bin/env python3
import json
from _common import parser_base, subsystem_ids, load_subsystem

def main()->int:
    parser_base("Continuity drift check").parse_args()
    drifting=[]
    for sid in subsystem_ids():
        s=load_subsystem(sid)
        if s.get("promotion_state")=="promoted" and s.get("release_readiness") in {"blocked","partial","attestation_pending"}:
            drifting.append(sid)
    state="drifting" if drifting else "stable"
    print(json.dumps({"continuity":state,"drifting_subsystems":drifting},indent=2))
    return 1 if drifting else 0
if __name__=="__main__": raise SystemExit(main())
