import subprocess,sys
from pathlib import Path

def test_reconcile_detects_missing(tmp_path: Path):
    ledger=tmp_path/'l.jsonl'; ledger.write_text('')
    cp=subprocess.run([sys.executable,'.abraxas/scripts/reconcile_subsystem_state.py','--ledger',str(ledger)],capture_output=True,text=True)
    assert cp.returncode==1
