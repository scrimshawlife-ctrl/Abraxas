import subprocess,sys

def test_governance_lint():
    cp=subprocess.run([sys.executable,'.abraxas/scripts/governance_lint.py'],capture_output=True,text=True)
    assert cp.returncode==0
