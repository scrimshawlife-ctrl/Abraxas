"""The lexicon's content fingerprint must identify CONTENT -- nothing else.

`manifest_sha256` is the lexicon's version identity: it is embedded in the generated module
and stored per generation. Two non-content fields were feeding it, so identical content
produced a different identity on every run:

    generated_at_utc   the wall clock
    inputs_dir         the input path AS SPELLED on the command line

Measured before the fix: with the clock pinned to a single value, generating from
`lexicon_sources` and from an absolute path to the same directory gave different hashes
(fe87ded0... vs d686f4d0...). A version that changes when nothing changed is not a version.

The rule is already established in this repo for engine identity -- see
`abraxas/yggdrasil/registry.py`: a hash covers identity only, never a timestamp.

These tests are the counterfactuals for the fix. Each of the first three FAILS against the
old implementation and passes against the new one; the last two guard against over-correcting
by throwing provenance away with the noise.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

EPOCH_A = "1700000000"   # 2023-11-14T22:13:20+00:00
EPOCH_B = "1800000000"   # 2027-01-15T08:00:00+00:00


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "w"
    root.mkdir()
    (root / "abraxas_ase" / "tools").mkdir(parents=True)
    repo = Path(__file__).resolve().parents[1]
    shutil.copytree(repo / "lexicon_sources", root / "lexicon_sources")
    for rel in (
        "abraxas_ase/__init__.py",
        "abraxas_ase/tools/__init__.py",
        "abraxas_ase/tools/lexicon_update.py",
    ):
        shutil.copy(repo / rel, root / rel)
    return root


def _generate(root: Path, in_arg: str, epoch: str) -> dict:
    """Run the generator and return {manifest, manifest_sha256, module_bytes}."""
    env = {**os.environ, "SOURCE_DATE_EPOCH": epoch}
    proc = subprocess.run(
        [sys.executable, "-m", "abraxas_ase.tools.lexicon_update",
         "--in", in_arg, "--out", "abraxas_ase"],
        cwd=str(root), capture_output=True, text=True, env=env,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return {
        "manifest": json.loads((root / "abraxas_ase" / "lexicon_manifest.json").read_text()),
        "hash": json.loads(proc.stdout)["manifest_sha256"],
        "module": (root / "abraxas_ase" / "lexicon_generated.py").read_bytes(),
    }


def test_fingerprint_ignores_how_the_input_path_is_spelled(tmp_path: Path) -> None:
    """The path on the command line is an invocation detail, not lexicon content."""
    root = _workspace(tmp_path)
    relative = _generate(root, "lexicon_sources", EPOCH_A)
    absolute = _generate(root, str((root / "lexicon_sources").resolve()), EPOCH_A)

    assert relative["manifest"]["inputs_dir"] != absolute["manifest"]["inputs_dir"], (
        "the test is not exercising the difference it claims to"
    )
    assert relative["hash"] == absolute["hash"], (
        "identical content hashed differently because the --in path was spelled differently: "
        f"{relative['hash']} vs {absolute['hash']}"
    )


def test_fingerprint_ignores_the_clock(tmp_path: Path) -> None:
    """Two different generation times, same content -> one identity."""
    root = _workspace(tmp_path)
    a = _generate(root, "lexicon_sources", EPOCH_A)
    b = _generate(root, "lexicon_sources", EPOCH_B)

    assert a["manifest"]["generated_at_utc"] != b["manifest"]["generated_at_utc"], (
        "the clock is not varying, so this test proves nothing"
    )
    assert a["hash"] == b["hash"], (
        "the wall clock leaked into the content fingerprint: "
        f"{a['hash']} vs {b['hash']}"
    )


def test_generated_module_is_byte_reproducible(tmp_path: Path) -> None:
    """The generated module's only variable input was the fingerprint comment."""
    root = _workspace(tmp_path)
    a = _generate(root, "lexicon_sources", EPOCH_A)
    b = _generate(root, "lexicon_sources", EPOCH_B)
    assert a["module"] == b["module"], (
        "lexicon_generated.py differs between two generations of identical content"
    )


def test_manifest_still_records_provenance(tmp_path: Path) -> None:
    """Guard against over-correcting: the noise leaves the HASH, not the artifact.

    A lexicon artifact that cannot say when and from where it was built is worse than one
    with an unstable hash.
    """
    root = _workspace(tmp_path)
    manifest = _generate(root, "lexicon_sources", EPOCH_A)["manifest"]

    assert manifest["generated_at_utc"].startswith("2023-11-14T22:13:20"), (
        "generated_at_utc should still record the pinned build time"
    )
    assert manifest["inputs_dir"] == "lexicon_sources"
    assert manifest["files"]["sha256"], "per-source content hashes are missing"
    assert manifest["merged"]["stopwords_sha256"], "merged content hash is missing"


def test_content_change_still_changes_the_fingerprint(tmp_path: Path) -> None:
    """The counterfactual that keeps the fingerprint meaningful: content must matter."""
    root = _workspace(tmp_path)
    before = _generate(root, "lexicon_sources", EPOCH_A)

    src = root / "lexicon_sources" / "subwords_core.txt"
    src.write_text(src.read_text(encoding="utf-8") + "\nwidget\n", encoding="utf-8")

    after = _generate(root, "lexicon_sources", EPOCH_A)
    assert after["hash"] != before["hash"], (
        "adding a token did not change the content fingerprint"
    )


def test_check_accepts_a_differently_spelled_path(tmp_path: Path) -> None:
    """`--check` asks 'is the content stale?', so the invocation form must not matter."""
    root = _workspace(tmp_path)
    _generate(root, "lexicon_sources", EPOCH_A)

    env = {**os.environ, "SOURCE_DATE_EPOCH": EPOCH_A}
    proc = subprocess.run(
        [sys.executable, "-m", "abraxas_ase.tools.lexicon_update",
         "--in", str((root / "lexicon_sources").resolve()),
         "--out", "abraxas_ase", "--check"],
        cwd=str(root), capture_output=True, text=True, env=env,
    )
    assert proc.returncode == 0, (
        "--check reported stale for identical content reached by a different path spelling:\n"
        + proc.stdout + proc.stderr
    )
