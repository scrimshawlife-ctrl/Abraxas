from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json
REQ={
"recommendation_execution_ledger":(Path("out/registry/self_build_recommendation_execution_ledger.latest.json"),"SelfBuildRecommendationExecutionLedger.v1"),
"batch_ledger":(Path("out/registry/self_build_batch_ledger.latest.json"),"SelfBuildBatchLedger.v1"),
"mutation_ledger":(Path("out/registry/self_build_mutation_ledger.latest.json"),"SelfBuildMutationLedgerCollection.v1"),
"rollback_ledger":(Path("out/registry/self_build_rollback_ledger.latest.json"),"SelfBuildRollbackLedger.v1"),
"scoring":(Path("out/registry/self_build_scoring.latest.json"),"SelfBuildScoring.v1"),
"batch_trends":(Path("out/registry/self_build_batch_trends.latest.json"),"SelfBuildBatchTrends.v1"),
}
def h(v:str)->str:return hashlib.sha256(v.encode()).hexdigest()
def c(o:Any)->str:return json.dumps(o,sort_keys=True,separators=(",",":"))
def fail(r:str):
 p={"schema_version":"SelfBuildEvolutionSummary.v1","status":"NOT_COMPUTABLE","reason":r,"authority":{"mutation":False,"promotion":False,"execution":False,"analysis_only":True}}
 p["canonical_hash"]=h(c(p));return p
def run_self_build_evolution_summary()->dict[str,Any]:
 d={}
 for k,(p,s) in REQ.items():
  if not p.exists(): return fail(f"MISSING:{k}")
  j=json.loads(p.read_text())
  if not isinstance(j,dict) or j.get("schema_version")!=s:return fail(f"INVALID:{k}")
  d[k]=j
 counts={"recommendation_executions":d["recommendation_execution_ledger"].get("entry_count",0),"batch_cycles":d["batch_ledger"].get("entry_count",0),"mutations":d["mutation_ledger"].get("entry_count",0),"rollbacks":d["rollback_ledger"].get("entry_count",0)}
 posture={"approval_state":"WAITING" if d["batch_trends"].get("latest_status")=="WAITING_FOR_APPROVAL" else "ACTIVE","mutation_state":"GATED","trend_state":d["batch_trends"].get("status","UNKNOWN"),"recommended_next_action":"REVIEW_PENDING_APPROVALS"}
 risks=list(d["batch_trends"].get("flagged_trends",[]))
 p={"schema_version":"SelfBuildEvolutionSummary.v1","status":"SUMMARY_READY","counts":counts,"posture":posture,"lineage":{"batch_ledger_hash":d["batch_ledger"].get("canonical_hash"),"mutation_ledger_hash":d["mutation_ledger"].get("canonical_hash"),"rollback_ledger_hash":d["rollback_ledger"].get("canonical_hash"),"scoring_hash":d["scoring"].get("canonical_hash"),"batch_trends_hash":d["batch_trends"].get("canonical_hash")},"risks":risks,"authority":{"mutation":False,"promotion":False,"execution":False,"analysis_only":True}}
 p["canonical_hash"]=h(c(p));return p
