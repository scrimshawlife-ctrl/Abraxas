from __future__ import annotations
from pathlib import Path
import json,hashlib
h=lambda v:hashlib.sha256(v.encode()).hexdigest();c=lambda o:json.dumps(o,sort_keys=True,separators=(",",":"))
REQ=[("out/registry/self_build_readiness_gate.latest.json","SelfBuildReadinessGate.v1"),("out/registry/self_build_operator_action_recommendations.latest.json","SelfBuildOperatorActionRecommendations.v1"),("out/registry/self_build_batch_trends.latest.json","SelfBuildBatchTrends.v1"),("out/registry/self_build_score_feedback.latest.json","SelfBuildScoreFeedback.v1")]
def run_self_build_auto_loop_plan():
 for p,s in REQ:
  P=Path(p)
  if not P.exists():
   x={"schema_version":"SelfBuildAutoLoopPlan.v1","status":"NOT_COMPUTABLE","blockers":[f"MISSING:{p}"],"authority":{"mutation":False,"promotion":False,"execution":False,"plan_only":True}};x["canonical_hash"]=h(c(x));return x
  j=json.loads(P.read_text())
  if j.get("schema_version")!=s:
   x={"schema_version":"SelfBuildAutoLoopPlan.v1","status":"NOT_COMPUTABLE","blockers":[f"INVALID:{p}"],"authority":{"mutation":False,"promotion":False,"execution":False,"plan_only":True}};x["canonical_hash"]=h(c(x));return x
 gate=json.loads(Path(REQ[0][0]).read_text())
 blocked=gate.get("status") not in {"READY_FOR_GUARDED_LOOP","WAITING_FOR_APPROVAL"}
 x={"schema_version":"SelfBuildAutoLoopPlan.v1","status":"BLOCKED" if blocked else "PLAN_READY","loop_mode":"GUARDED_OPERATOR_LOOP","planned_steps":["run_batch_cycle","read_trends","read_score_feedback","generate_recommendations","wait_for_operator"],"allowed_actions":["RUN_BATCH","HOLD","APPROVE_ONE","REJECT_TARGET"],"forbidden_actions":["DIRECT_ARTIFACT_MUTATION","AUTO_APPROVAL","PROMOTION","ROLLBACK_WITHOUT_OPERATOR"],"blockers":[] if not blocked else ["READINESS_NOT_MET"],"authority":{"mutation":False,"promotion":False,"execution":False,"plan_only":True}}
 x["canonical_hash"]=h(c(x));return x
