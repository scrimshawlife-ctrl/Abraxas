from __future__ import annotations
from pathlib import Path
import json,hashlib
h=lambda v:hashlib.sha256(v.encode()).hexdigest();c=lambda o:json.dumps(o,sort_keys=True,separators=(",",":"))
REQ=[("out/registry/self_build_evolution_summary.latest.json","SelfBuildEvolutionSummary.v1"),("out/registry/self_build_readiness_gate.latest.json","SelfBuildReadinessGate.v1"),("out/registry/self_build_auto_loop_plan.latest.json","SelfBuildAutoLoopPlan.v1"),("out/registry/self_build_operator_action_recommendations.latest.json","SelfBuildOperatorActionRecommendations.v1"),("out/registry/self_build_batch_cycle.latest.json","SelfBuildBatchCycle.v1")]
def run_self_build_operator_packet():
 d={}
 for p,s in REQ:
  P=Path(p)
  if not P.exists():
   x={"schema_version":"SelfBuildOperatorPacket.v1","status":"NOT_COMPUTABLE","authority":{"mutation":False,"promotion":False,"execution":False,"operator_display_only":True}};x["canonical_hash"]=h(c(x));return x
  j=json.loads(P.read_text());
  if j.get("schema_version")!=s:
   x={"schema_version":"SelfBuildOperatorPacket.v1","status":"NOT_COMPUTABLE","authority":{"mutation":False,"promotion":False,"execution":False,"operator_display_only":True}};x["canonical_hash"]=h(c(x));return x
  d[p]=j
 recs=d[REQ[3][0]].get("actions",[])
 x={"schema_version":"SelfBuildOperatorPacket.v1","status":"PACKET_READY","headline_state":d[REQ[4][0]].get("status"),"recommended_next_action":(recs[0]["action_type"] if recs else "NONE"),"top_recommendations":recs[:3],"readiness_status":d[REQ[1][0]].get("status"),"approval_state":d[REQ[0][0]].get("posture",{}).get("approval_state"),"risks":d[REQ[0][0]].get("risks",[]),"artifact_pointers":[p for p,_ in REQ],"authority":{"mutation":False,"promotion":False,"execution":False,"operator_display_only":True}}
 x["canonical_hash"]=h(c(x));return x
