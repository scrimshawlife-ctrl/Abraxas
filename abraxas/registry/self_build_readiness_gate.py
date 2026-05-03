from __future__ import annotations
from pathlib import Path
from typing import Any
import json,hashlib
REQ={"evolution":("out/registry/self_build_evolution_summary.latest.json","SelfBuildEvolutionSummary.v1"),"cycle":("out/registry/self_build_batch_cycle.latest.json","SelfBuildBatchCycle.v1"),"trends":("out/registry/self_build_batch_trends.latest.json","SelfBuildBatchTrends.v1"),"recs":("out/registry/self_build_operator_action_recommendations.latest.json","SelfBuildOperatorActionRecommendations.v1"),"feedback":("out/registry/self_build_score_feedback.latest.json","SelfBuildScoreFeedback.v1"),"card":("out/operator/operator_closure_card.latest.json","OperatorClosureCard.v1"),"validator":("out/registry/binding_validator_run.latest.json","BindingValidatorRun.v1")}
h=lambda v:hashlib.sha256(v.encode()).hexdigest();c=lambda o:json.dumps(o,sort_keys=True,separators=(",",":"))
def fail(r):p={"schema_version":"SelfBuildReadinessGate.v1","status":"NOT_COMPUTABLE","blockers":[r],"authority":{"mutation":False,"promotion":False,"execution":False,"analysis_only":True}};p["canonical_hash"]=h(c(p));return p
def run_self_build_readiness_gate()->dict[str,Any]:
 d={}
 for k,(p,s) in REQ.items():
  P=Path(p)
  if not P.exists():return fail(f"MISSING:{k}")
  j=json.loads(P.read_text())
  if not isinstance(j,dict) or j.get("schema_version")!=s:return fail(f"INVALID:{k}")
  d[k]=j
 gates={"validator_pass":d["validator"].get("overall_status")=="PASS","operator_green":d["card"].get("health")=="GREEN","trends_available":d["trends"].get("status")=="OK","recommendations_available":d["recs"].get("status")=="OK","feedback_available":d["feedback"].get("status")=="OK","approval_pending":d["cycle"].get("status")=="WAITING_FOR_APPROVAL","mutation_path_gated":True}
 blockers=[k for k,v in gates.items() if k not in {"approval_pending"} and not v]
 status="READY_FOR_GUARDED_LOOP"
 if gates["approval_pending"]:status="WAITING_FOR_APPROVAL"
 if blockers:status="NOT_READY"
 p={"schema_version":"SelfBuildReadinessGate.v1","status":status,"gates":gates,"blockers":sorted(blockers),"authority":{"mutation":False,"promotion":False,"execution":False,"analysis_only":True}}
 p["canonical_hash"]=h(c(p));return p
