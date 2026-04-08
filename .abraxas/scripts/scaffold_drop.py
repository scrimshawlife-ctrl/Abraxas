#!/usr/bin/env python3
from pathlib import Path
from _common import parser_base

def main() -> int:
    p=parser_base("Scaffold drop envelope")
    p.add_argument("--out", required=True)
    args=p.parse_args()
    tpl=Path(__file__).resolve().parents[1]/"templates"/"code_drop_envelope.md"
    Path(args.out).write_text(tpl.read_text())
    print(args.out)
    return 0
if __name__=="__main__":
    raise SystemExit(main())
