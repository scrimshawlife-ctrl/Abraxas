from __future__ import annotations

import os
import tempfile

from abraxas.oracle.v2.evidence import attach_evidence_pointers, attach_evidence_from_files


def test_attach_evidence_pointers_writes_paths_and_hashes():
    env = {"oracle_signal": {}}
    out = attach_evidence_pointers(
        envelope=env,
        paths={"news": "var/evidence/news.json"},
        hashes={"news": "abc"},
    )
    assert out["oracle_signal"]["evidence"]["paths"]["news"] == "var/evidence/news.json"
    assert out["oracle_signal"]["evidence"]["hashes"]["news"] == "abc"


def test_attach_evidence_from_files_attaches_only_existing():
    with tempfile.TemporaryDirectory() as td:
        good = os.path.join(td, "good.txt")
        with open(good, "w", encoding="utf-8") as f:
            f.write("hello")
        missing = os.path.join(td, "missing.txt")

        env = {"oracle_signal": {}}
        out = attach_evidence_from_files(
            envelope=env,
            files={"good": good, "missing": missing},
            compute_hashes=True,
        )
        ev = out["oracle_signal"]["evidence"]
        assert "good" in ev["paths"]
        assert "missing" not in ev["paths"]
        assert "good" in ev["hashes"]


def test_attach_evidence_from_files_no_hashes_when_disabled():
    with tempfile.TemporaryDirectory() as td:
        good = os.path.join(td, "good.txt")
        with open(good, "w", encoding="utf-8") as f:
            f.write("hello")

        env = {"oracle_signal": {}}
        out = attach_evidence_from_files(
            envelope=env,
            files={"good": good},
            compute_hashes=False,
        )
        ev = out["oracle_signal"]["evidence"]
        assert "paths" in ev
        assert "hashes" not in ev
