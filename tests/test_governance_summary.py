import subprocess,sys,json

def test_governance_summary_json():
    cp=subprocess.run([sys.executable,'.abraxas/scripts/governance_summary.py'],capture_output=True,text=True)
    assert cp.returncode==0
    assert 'subsystems' in json.loads(cp.stdout)


def test_aalmanac_tau_summary_reports_its_runtime_lane():
    cp=subprocess.run([sys.executable,'.abraxas/scripts/governance_summary.py'],capture_output=True,text=True)
    assert cp.returncode==0, cp.stderr
    rows=json.loads(cp.stdout)['subsystems']
    tau=[row for row in rows if row['subsystem']=='aalmanac_tau']
    assert len(tau)==1
    assert tau[0]['lane']=='forecast-active'
