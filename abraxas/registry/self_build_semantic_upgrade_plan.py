from __future__ import annotations
from pathlib import Path
from typing import Any
import json,hashlib
REQ=[("out/registry/self_build_final_stack_result.latest.json","SelfBuildFinalStackResult.v1"),("out/registry/self_build_evolution_summary.latest.json","SelfBuildEvolutionSummary.v1"),("out/registry/self_build_score_feedback.latest.json","SelfBuildScoreFeedback.v1"),("out/operator/self_build_operator_packet.latest.json","SelfBuildOperatorPacket.v1"),("out/oracle/oracle_signal_packet.latest.json",None),("out/scoring/brier_scoring.latest.json",None),("out/canary/canary_activation_packet.latest.json",None)]
h=lambda v:hashlib.sha256(v.encode()).hexdigest();c=lambda o:json.dumps(o,sort_keys=True,separators=(",",":"))
def _depth(path:str,obj:dict[str,Any])->str:
 s=str(obj.get('status',''))
 if s=='NOT_COMPUTABLE':return 'STUB'
 if path.endswith('oracle_signal_packet.latest.json'):
  return 'SEMANTIC_COMPUTABLE' if obj.get('schema_version')=='OracleSignalPacket.v1' and isinstance(obj.get('signal_count'),int) and isinstance(obj.get('structural_keys'),list) else 'PLACEHOLDER_COMPUTABLE'
 if path.endswith('brier_scoring.latest.json'):
  return 'SEMANTIC_COMPUTABLE' if obj.get('schema_version')=='BrierScoringRun.v1' and isinstance(obj.get('scored_count'),int) and 'mean_brier' in obj else 'PLACEHOLDER_COMPUTABLE'
 if path.endswith('canary_activation_packet.latest.json'):
  return 'SEMANTIC_COMPUTABLE' if obj.get('schema_version')=='CanaryActivationPacket.v1' and isinstance(obj.get('entries'),list) else 'PLACEHOLDER_COMPUTABLE'
 if s=='COMPUTABLE' and obj.get('upgraded_from')=='STUB':return 'PLACEHOLDER_COMPUTABLE'
 return 'SEMANTIC_COMPUTABLE'
def run_self_build_semantic_upgrade_plan()->dict[str,Any]:
 loaded={}
 for p,s in REQ:
  P=Path(p)
  if not P.exists():
   x={"schema_version":"SelfBuildSemanticUpgradePlan.v1","status":"NOT_COMPUTABLE","reason":f"MISSING:{p}","targets":[],"authority":{"mutation":False,"promotion":False,"execution":False,"plan_only":True}};x['canonical_hash']=h(c(x));return x
  j=json.loads(P.read_text())
  if s and j.get('schema_version')!=s:
   x={"schema_version":"SelfBuildSemanticUpgradePlan.v1","status":"NOT_COMPUTABLE","reason":f"INVALID:{p}","targets":[],"authority":{"mutation":False,"promotion":False,"execution":False,"plan_only":True}};x['canonical_hash']=h(c(x));return x
  loaded[p]=j
 targets=[]
 mapping=[('out/oracle/oracle_signal_packet.latest.json','oracle','UPGRADE_SIGNAL_SEMANTICS'),('out/scoring/brier_scoring.latest.json','scoring','UPGRADE_SCORING_SEMANTICS'),('out/canary/canary_activation_packet.latest.json','canary','UPGRADE_CANARY_SEMANTICS')]
 pri={'STUB':'HIGH','PLACEHOLDER_COMPUTABLE':'MEDIUM','SEMANTIC_COMPUTABLE':'LOW'}
 for p,m,u in mapping:
  d=_depth(p,loaded[p])
  targets.append({"target_path":p,"current_depth":d,"recommended_module":m,"upgrade_type":u,"priority":pri[d],"blockers":[] if d!='SEMANTIC_COMPUTABLE' else ["ALREADY_SEMANTIC"],"validation_commands":["python scripts/run_binding_validator.py","python scripts/run_operator_closure_card.py","python scripts/run_invariance_harness.py"]})
 targets=sorted(targets,key=lambda t:(["HIGH","MEDIUM","LOW"].index(t['priority']),t['target_path']))
 x={"schema_version":"SelfBuildSemanticUpgradePlan.v1","status":"PLAN_READY","targets":targets,"authority":{"mutation":False,"promotion":False,"execution":False,"plan_only":True}}
 x['canonical_hash']=h(c(x));return x
