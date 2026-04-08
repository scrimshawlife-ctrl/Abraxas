#!/usr/bin/env python3
import json
from pathlib import Path
from _common import parser_base, subsystem_ids, load_subsystem, now_iso

def main()->int:
    p=parser_base("Generate release manifest")
    p.add_argument("--out", required=True)
    a=p.parse_args()
    gated=[]
    for sid in subsystem_ids():
        s=load_subsystem(sid)
        if s.get("drop_status")=="active" and s.get("release_readiness")=="gated":
            gated.append(sid)
    manifest={"record_type":"release_manifest","timestamp":now_iso(),"subsystems":gated,"status":"SUCCESS","provenance":{"source":"repo-local"},"correlation_pointers":[]}
    Path(a.out).write_text(json.dumps(manifest,indent=2))
    print(a.out)
    return 0
if __name__=="__main__": raise SystemExit(main())
