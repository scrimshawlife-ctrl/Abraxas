#!/usr/bin/env python3
from _common import parser_base, subsystem_ids, load_subsystem

def main() -> int:
    p = parser_base("Subsystem preflight eligibility checks")
    p.add_argument("--subsystem", required=True)
    p.add_argument("--change-class")
    args = p.parse_args()
    if args.subsystem not in subsystem_ids():
        print("NOT_ELIGIBLE: subsystem not in registry")
        return 1
    data = load_subsystem(args.subsystem)
    missing=[f for f in ["code_authorized","drop_status","release_readiness"] if f not in data]
    if missing:
        print(f"NOT_ELIGIBLE: missing fields {missing}")
        return 1
    if args.change_class:
        restricted = set(data.get("restricted_change_classes", []))
        allowed = set(data.get("allowed_change_classes", []))
        if args.change_class in restricted:
            print(f"NOT_ELIGIBLE: restricted change class {args.change_class}")
            return 1
        if allowed and args.change_class not in allowed:
            print(f"NOT_ELIGIBLE: unsupported change class {args.change_class}")
            return 1
    print("ELIGIBLE" if data["code_authorized"] else "NOT_ELIGIBLE")
    return 0 if data["code_authorized"] else 1

if __name__=="__main__":
    raise SystemExit(main())
