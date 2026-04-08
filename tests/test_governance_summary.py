import subprocess,sys,json

def test_governance_summary_json():
    cp=subprocess.run([sys.executable,'.abraxas/scripts/governance_summary.py'],capture_output=True,text=True)
    assert cp.returncode==0
    assert 'subsystems' in json.loads(cp.stdout)
