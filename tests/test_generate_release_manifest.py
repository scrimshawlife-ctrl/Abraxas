import subprocess,sys,json
from pathlib import Path

def test_generate_manifest(tmp_path: Path):
    out=tmp_path/'manifest.json'
    cp=subprocess.run([sys.executable,'.abraxas/scripts/generate_release_manifest.py','--out',str(out)],capture_output=True,text=True)
    assert cp.returncode==0
    data=json.loads(out.read_text())
    assert data['record_type']=='release_manifest'
