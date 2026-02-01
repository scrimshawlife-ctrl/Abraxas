import copy
import json
import os
import subprocess
import sys

from abraxas.mda.drift_classifier import classify_drift


def _load(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write(path: str, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def test_mda_practice_golden_12run_invariance(tmp_path):
    exp = _load("tests/golden/mda_practice_expected.json")
    out_dir = tmp_path / "mda_practice"

    cmd = [
        sys.executable,
        "-m",
        "abraxas.mda.practice_run",
        "--repeat",
        str(exp["expected"]["repeat"]),
        "--mode",
        exp["expected"]["mode"],
        "--env",
        exp["expected"]["env"],
        "--seed",
        str(exp["expected"]["seed"]),
        "--inputs",
        exp["expected"]["inputs"],
        "--toggles",
        exp["expected"]["toggles"],
        "--out-dir",
        str(out_dir),
        "--emit-signal-v2",
        "--signal-schema-check",
        "--ledger",
        "--emit-jsonl",
    ]
    r = subprocess.run(cmd, check=False, capture_output=True, text=True)
    assert r.returncode == 0, f"practice runner failed:\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    inv_path = os.path.join(str(out_dir), "invariance_report.json")
    assert os.path.exists(inv_path), "missing invariance_report.json"
    inv = _load(inv_path)

    if exp["assertions"]["require_invariance_report"]:
        assert inv.get("canon_invariant") is True
        assert inv.get("drift_class") == exp["assertions"]["drift_class"]

    # Ledger hash pinning (tests-only golden update gate)
    ledger_path = os.path.join(str(out_dir), "session_ledger.json")
    assert os.path.exists(ledger_path), "missing session_ledger.json"
    ledger = _load(ledger_path)
    actual_hash = ledger.get("session_ledger_hash") or ledger.get("hash") or None
    if actual_hash is None:
        # If SessionLedger doesn't embed its own hash, compute a stable one by re-dumping.
        import hashlib

        blob = json.dumps(ledger, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        actual_hash = hashlib.sha256(blob).hexdigest()

    expected_hash = exp["expected"].get("expected_session_ledger_hash")
    if expected_hash is None:
        # Not pinned yet: allow pass, but provide deterministic guidance.
        print(
            "[MDA_GOLDEN_PIN] expected_session_ledger_hash is not pinned.\n"
            "  To pin explicitly (tests-only): ABRAXAS_GOLDEN_UPDATE=1 pytest -q tests/test_mda_golden_12run.py\n"
            f"  Suggested pin: {actual_hash}\n"
        )
    else:
        if expected_hash != actual_hash:
            diag = classify_drift(
                invariance_report=inv,
                expected_session_ledger_hash=expected_hash,
                actual_session_ledger_hash=actual_hash,
            )
            allow_update = os.environ.get("ABRAXAS_GOLDEN_UPDATE", "") == "1"
            if allow_update:
                exp2 = copy.deepcopy(exp)
                exp2["expected"]["expected_session_ledger_hash"] = actual_hash
                _write("tests/golden/mda_practice_expected.json", exp2)
            else:
                raise AssertionError(
                    "Golden hash mismatch.\n"
                    f"expected_session_ledger_hash={expected_hash}\n"
                    f"actual_session_ledger_hash={actual_hash}\n"
                    f"classification={diag.drift_class}\n"
                    f"reason={diag.reason}\n"
                    "To update goldens (tests only): ABRAXAS_GOLDEN_UPDATE=1 pytest -q\n"
                )

    # Ensure signal_v2 exists in run_01
    if exp["assertions"]["require_signal_v2"]:
        sig_path = os.path.join(str(out_dir), "run_01", "signal_v2.json")
        assert os.path.exists(sig_path), "missing run_01/signal_v2.json"
        sig = _load(sig_path)
        assert "oracle_signal_v2" in sig
        assert "mda_v1_1" in sig["oracle_signal_v2"]
        assert sig["oracle_signal_v2"]["meta"]["slice_hash"]

