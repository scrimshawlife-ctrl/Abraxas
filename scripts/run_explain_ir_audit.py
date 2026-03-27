#!/usr/bin/env python3
from __future__ import annotations

import json

from abx.explain.explainIrAudit import run_explain_ir_audit


def main() -> None:
    print(json.dumps(run_explain_ir_audit(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
