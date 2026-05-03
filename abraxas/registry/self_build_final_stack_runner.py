from __future__ import annotations
import json,hashlib
from abraxas.registry.self_build_evolution_summary import run_self_build_evolution_summary
from abraxas.registry.self_build_readiness_gate import run_self_build_readiness_gate
from abraxas.registry.self_build_auto_loop_plan import run_self_build_auto_loop_plan
from abraxas.operator.self_build_operator_packet import run_self_build_operator_packet
h=lambda v:hashlib.sha256(v.encode()).hexdigest();c=lambda o:json.dumps(o,sort_keys=True,separators=(",",":"))
def run_self_build_final_stack_runner():
 s=run_self_build_evolution_summary();r=run_self_build_readiness_gate();a=run_self_build_auto_loop_plan();o=run_self_build_operator_packet()
 ok=all(x.get("status") in {"SUMMARY_READY","WAITING_FOR_APPROVAL","READY_FOR_GUARDED_LOOP","NOT_READY","PLAN_READY","BLOCKED","PACKET_READY"} for x in [s,r,a,o]) and o.get("status")=="PACKET_READY"
 p={"schema_version":"SelfBuildFinalStackResult.v1","status":"FINAL_STACK_READY" if ok else "NOT_COMPUTABLE","generated_artifacts":["out/registry/self_build_evolution_summary.latest.json","out/registry/self_build_readiness_gate.latest.json","out/registry/self_build_auto_loop_plan.latest.json","out/operator/self_build_operator_packet.latest.json"],"summary_hash":s.get("canonical_hash"),"readiness_hash":r.get("canonical_hash"),"auto_loop_plan_hash":a.get("canonical_hash"),"operator_packet_hash":o.get("canonical_hash"),"authority_integrity":True,"authority":{"mutation":False,"promotion":False,"execution":False,"final_stack_orchestration_only":True}}
 p["canonical_hash"]=h(c(p));return p
