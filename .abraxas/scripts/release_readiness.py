#!/usr/bin/env python3
from _common import parser_base, load_subsystem

def main()->int:
    p=parser_base("Release readiness checks")
    p.add_argument("--subsystem", required=True)
    p.add_argument("--receipts", nargs="*", default=[])
    a=p.parse_args()
    s=load_subsystem(a.subsystem)
    missing=[r for r in s.get("required_receipts",[]) if r not in a.receipts]
    if s.get("release_readiness")=="blocked" or missing:
        print(f"BLOCKED missing={missing}")
        return 1
    print("READY")
    return 0
if __name__=="__main__": raise SystemExit(main())
