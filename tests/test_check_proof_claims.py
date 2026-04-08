import subprocess,sys
from pathlib import Path

def test_proof_claims_detects_forbidden(tmp_path: Path):
    f=tmp_path/'bad.md'
    f.write_text('this is production-ready')
    cp=subprocess.run([sys.executable,'.abraxas/scripts/check_proof_claims.py','--path',str(tmp_path)],capture_output=True,text=True)
    assert cp.returncode==1
