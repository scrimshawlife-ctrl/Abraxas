#!/usr/bin/env python3
from pathlib import Path
from _common import parser_base, subsystem_ids

def main()->int:
    parser_base("Registry consistency").parse_args()
    base=Path(__file__).resolve().parents[1]/"subsystems"
    missing=[]
    for sid in subsystem_ids():
        if not (base/f"{sid}.yaml").exists():
            missing.append(sid)
    if missing:
        print("MISSING", ",".join(missing))
        return 1
    print("OK")
    return 0
if __name__=="__main__": raise SystemExit(main())
