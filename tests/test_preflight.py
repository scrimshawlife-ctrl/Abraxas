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


def test_preflight_aalmanac_tau_accepts_test_only_coverage_class():
    cp = subprocess.run(
        [
            sys.executable,
            '.abraxas/scripts/preflight.py',
            '--subsystem',
            'aalmanac_tau',
            '--change-class',
            'test_only_coverage',
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0
    assert cp.stdout.strip() == 'ELIGIBLE'


def test_preflight_aalmanac_tau_requires_explicit_change_class():
    cp = subprocess.run(
        [
            sys.executable,
            '.abraxas/scripts/preflight.py',
            '--subsystem',
            'aalmanac_tau',
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 1
    assert cp.stdout.strip() == 'NOT_ELIGIBLE: change class required'


def test_preflight_aalmanac_tau_rejects_runtime_changes():
    cp = subprocess.run(
        [
            sys.executable,
            '.abraxas/scripts/preflight.py',
            '--subsystem',
            'aalmanac_tau',
            '--change-class',
            'forecast_active_change',
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 1
    assert 'unsupported change class' in cp.stdout
