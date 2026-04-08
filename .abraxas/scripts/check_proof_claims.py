#!/usr/bin/env python3
from pathlib import Path
from _common import parser_base, load_yaml

def main() -> int:
    p=parser_base("Proof claim language checks")
    p.add_argument("--path", default=".")
    args=p.parse_args()
    terms=load_yaml(Path(__file__).resolve().parents[1]/"governance"/"forbidden_terms.yaml")["forbidden_terms"]
    violations=[]
    for path in Path(args.path).rglob("*.md"):
        text=path.read_text(errors="ignore").lower()
        for t in terms:
            if t.lower() in text:
                violations.append((str(path),t))
    if violations:
        for v in violations:
            print(f"VIOLATION {v[0]} -> {v[1]}")
        return 1
    print("OK")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
