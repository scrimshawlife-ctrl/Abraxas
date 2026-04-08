import subprocess,sys,json

def test_repo_status_structured():
    cp=subprocess.run([sys.executable,'.abraxas/scripts/repo_status.py'],capture_output=True,text=True)
    assert cp.returncode==0
    assert 'counts' in json.loads(cp.stdout)
