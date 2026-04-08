import subprocess,sys

def test_registry_consistency():
    cp=subprocess.run([sys.executable,'.abraxas/scripts/registry_consistency.py'],capture_output=True,text=True)
    assert cp.returncode==0
