import subprocess,sys,json
from pathlib import Path

def test_append_rejects_invalid(tmp_path: Path):
    rec=tmp_path/'r.json'; rec.write_text(json.dumps({'record_type':'x'}))
    ledger=tmp_path/'l.jsonl'
    cp=subprocess.run([sys.executable,'.abraxas/scripts/append_governance_record.py','--record',str(rec),'--ledger',str(ledger)],capture_output=True,text=True)
    assert cp.returncode==1
