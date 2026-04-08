import subprocess,sys

def test_release_readiness_blocked_without_receipts():
    cp=subprocess.run([sys.executable,'.abraxas/scripts/release_readiness.py','--subsystem','forecast_portfolio_simulation_v0_1'],capture_output=True,text=True)
    assert cp.returncode==1
