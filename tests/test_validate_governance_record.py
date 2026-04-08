import subprocess,sys,json
from pathlib import Path

def test_validate_record(tmp_path: Path):
    rec=tmp_path/'record.json'
    rec.write_text(json.dumps({'record_type':'promotion_decision','timestamp':'2026-01-01T00:00:00Z','status':'SUCCESS','provenance':{},'correlation_pointers':[]}))
    cp=subprocess.run([sys.executable,'.abraxas/scripts/validate_governance_record.py','--record',str(rec)],capture_output=True,text=True)
    assert cp.returncode==0
