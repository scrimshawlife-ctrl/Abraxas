#!/usr/bin/env python3
from _common import parser_base, load_subsystem

def main()->int:
    p=parser_base("Proof requirements lookup")
    p.add_argument("--subsystem", required=True)
    p.add_argument("--change-class", default="default")
    a=p.parse_args()
    s=load_subsystem(a.subsystem)
    req=s.get("receipt_overrides",{}).get(a.change_class, s.get("required_receipts",[]))
    print("
".join(req))
    return 0
if __name__=="__main__": raise SystemExit(main())
