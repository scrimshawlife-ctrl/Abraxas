import subprocess,sys,json

def test_continuity_drift_stable_or_drifting():
    cp=subprocess.run([sys.executable,'.abraxas/scripts/continuity_drift_check.py'],capture_output=True,text=True)
    assert cp.returncode in (0,1)
    assert json.loads(cp.stdout)['continuity'] in ('stable','drifting')
