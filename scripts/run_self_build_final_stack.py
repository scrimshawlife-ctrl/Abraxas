from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from abraxas.registry.self_build_final_stack_runner import run_self_build_final_stack_runner

if __name__ == '__main__':
    lineage_path = Path('out/semantic/semantic_lineage_report.latest.json')
    if not lineage_path.exists():
        try:
            from abraxas.semantic.lineage_report import build_semantic_lineage_report
            lineage_path.parent.mkdir(parents=True, exist_ok=True)
            lineage_path.write_text(json.dumps(build_semantic_lineage_report(), indent=2, sort_keys=True) + '\n', encoding='utf-8')
        except Exception:
            pass
    try:
        import subprocess
        subprocess.run(["python", "scripts/run_readiness_policy_ledger.py"], check=False)
        subprocess.run(["python", "scripts/run_readiness_policy_trends.py"], check=False)
    except Exception:
        pass
    r = run_self_build_final_stack_runner()
    p = Path('out/registry/self_build_final_stack_result.latest.json')
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(r, indent=2, sort_keys=True) + '\n')
