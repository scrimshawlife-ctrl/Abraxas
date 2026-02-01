import json
import os
import subprocess
import sys


def _load(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_mda_practice_golden_12run_invariance(tmp_path):
    exp = _load("tests/golden/mda_practice_expected.json")
    out_dir = tmp_path / "mda_practice"

    # Run the sandbox practice rig (module path)
    cmd = [
        sys.executable,
        "-m",
        "abraxas.sandbox.mda_practice",
        "--out",
        str(out_dir),
        "--repeat",
        str(exp["expected"]["repeat"]),
        "--mode",
        exp["expected"]["mode"],
        "--env",
        exp["expected"]["env"],
        "--seed",
        str(exp["expected"]["seed"]),
        "--run-at",
        exp["expected"]["run_at"],
        "--fixture",
        exp["expected"]["fixture"],
        "--bundle",
        exp["expected"]["bundle"],
        "--toggles",
        exp["expected"]["toggles"],
        "--strict-budgets",
        "--emit-md",
        "--emit-signal-v2",
        "--signal-schema-check",
        "--ledger",
        "--emit-jsonl",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"practice runner failed:\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    inv_path = os.path.join(str(out_dir), "invariance_report.json")
    assert os.path.exists(inv_path), "missing invariance_report.json"
    inv = _load(inv_path)

    if exp["assertions"]["require_invariance_report"]:
        assert inv.get("canon_invariant") is True
        assert inv.get("drift_class") == exp["assertions"]["drift_class"]

    # Ensure signal_v2 exists in run_01
    if exp["assertions"]["require_signal_v2"]:
        sig_path = os.path.join(str(out_dir), "run_01", "signal_v2.json")
        assert os.path.exists(sig_path), "missing run_01/signal_v2.json"
        sig = _load(sig_path)
        assert "oracle_signal_v2" in sig
        assert "mda_v1_1" in sig["oracle_signal_v2"]
        assert sig["oracle_signal_v2"]["meta"]["slice_hash"]

    # Ensure replay stream exists
    jsonl_path = os.path.join(str(out_dir), "replay.jsonl")
    assert os.path.exists(jsonl_path), "missing replay.jsonl"
    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    assert len(lines) == exp["expected"]["repeat"]

