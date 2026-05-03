from pathlib import Path
from abraxas.registry.self_build_semantic_upgrade_plan import run_self_build_semantic_upgrade_plan

def test_schema_authority_determinism():
 a=run_self_build_semantic_upgrade_plan();b=run_self_build_semantic_upgrade_plan();
 assert a['schema_version']=='SelfBuildSemanticUpgradePlan.v1';assert a['authority']=={"mutation":False,"promotion":False,"execution":False,"plan_only":True};assert a['canonical_hash']==b['canonical_hash']

def test_fail_closed_missing_artifact():
 p=Path('out/operator/self_build_operator_packet.latest.json');bak=Path(str(p)+'.bak')
 if p.exists():bak.write_text(p.read_text());p.unlink()
 try:
  r=run_self_build_semantic_upgrade_plan();assert r['status']=='NOT_COMPUTABLE'
 finally:
  if bak.exists():p.write_text(bak.read_text());bak.unlink()
