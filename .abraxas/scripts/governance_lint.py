#!/usr/bin/env python3
from pathlib import Path
from _common import parser_base, subsystem_ids, load_subsystem
REQ=["canon_status","tier","drop_status","code_authorized","lane","promotion_state","revocation_state","release_readiness","allowed_change_classes","restricted_change_classes","required_receipts","receipt_overrides","promotion_requirements","revocation_triggers","default_completion_if_no_receipts","stop_if_missing","notes"]

def main()->int:
    parser_base("Governance lint").parse_args()
    bad=[]
    for sid in subsystem_ids():
        data=load_subsystem(sid)
        miss=[k for k in REQ if k not in data]
        if miss:
            bad.append((sid,miss))
    if bad:
        for sid,miss in bad:
            print(f"{sid}: missing {miss}")
        return 1
    print("OK")
    return 0
if __name__=="__main__": raise SystemExit(main())
