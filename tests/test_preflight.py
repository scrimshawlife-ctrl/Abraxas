import subprocess
import sys


def test_preflight_oracle():
    cp = subprocess.run(
        [sys.executable, '.abraxas/scripts/preflight.py', '--subsystem', 'oracle_signal_layer_v2'],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0
    assert 'ELIGIBLE' in cp.stdout


def test_preflight_change_class_restricted_for_mbom():
    cp = subprocess.run(
        [
            sys.executable,
            '.abraxas/scripts/preflight.py',
            '--subsystem',
            'mbom_v1',
            '--change-class',
            'forecast_active_change',
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 1
    assert 'restricted change class' in cp.stdout
