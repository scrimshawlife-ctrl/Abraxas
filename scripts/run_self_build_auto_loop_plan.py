from __future__ import annotations
import json,sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from abraxas.registry.self_build_auto_loop_plan import run_self_build_auto_loop_plan
if __name__=='__main__':
 r=run_self_build_auto_loop_plan();p=Path('out/registry/self_build_auto_loop_plan.latest.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
