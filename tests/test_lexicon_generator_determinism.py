from __future__ import annotations

import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Pinned generation time (reproducible-builds convention).
#
# The manifest records when it was generated ("generated_at_utc") and that value is
# hashed into manifest_sha256, which is then embedded in the generated module. With a
# wall clock, two runs over identical inputs cannot be byte-identical -- they differ
# whenever they straddle a second boundary, which made this test flap (~1 in 5 runs).
# SOURCE_DATE_EPOCH pins it. See abraxas_ase/tools/lexicon_update.py.
SOURCE_DATE_EPOCH = "1700000000"  # 2023-11-14T22:13:20+00:00
PINNED_ISO = "2023-11-14T22:13:20+00:00"


def _run(cmd: list[str], cwd: Path, env: dict[str, str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout + p.stderr)


def test_lexicon_generator_is_deterministic(tmp_path: Path) -> None:
    # Arrange: copy minimal repo structure into temp
    root = tmp_path / "w"
    root.mkdir()
    (root / "abraxas_ase").mkdir()
    (root / "abraxas_ase" / "tools").mkdir(parents=True)

    repo = Path(__file__).resolve().parents[1]
    shutil.copytree(repo / "lexicon_sources", root / "lexicon_sources")
    shutil.copy(repo / "abraxas_ase" / "__init__.py", root / "abraxas_ase" / "__init__.py")
    shutil.copy(repo / "abraxas_ase" / "tools" / "__init__.py", root / "abraxas_ase" / "tools" / "__init__.py")
    shutil.copy(repo / "abraxas_ase" / "tools" / "lexicon_update.py", root / "abraxas_ase" / "tools" / "lexicon_update.py")

    # Run twice with the generation time pinned, and with the interpreter running the
    # test rather than a PATH lookup for "python" (which can resolve elsewhere).
    env = {**os.environ, "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH}
    cmd = [
        sys.executable,
        "-m",
        "abraxas_ase.tools.lexicon_update",
        "--in",
        "lexicon_sources",
        "--out",
        "abraxas_ase",
    ]
    rc1, out1 = _run(cmd, root, env)
    assert rc1 == 0, out1
    gen1 = (root / "abraxas_ase" / "lexicon_generated.py").read_text(encoding="utf-8")
    man1 = (root / "abraxas_ase" / "lexicon_manifest.json").read_text(encoding="utf-8")

    rc2, out2 = _run(cmd, root, env)
    assert rc2 == 0, out2
    gen2 = (root / "abraxas_ase" / "lexicon_generated.py").read_text(encoding="utf-8")
    man2 = (root / "abraxas_ase" / "lexicon_manifest.json").read_text(encoding="utf-8")

    assert gen1 == gen2
    assert man1 == man2

    # The pinned time must actually be honoured -- otherwise "deterministic" could be
    # satisfied by a generator that quietly stopped recording provenance at all.
    assert PINNED_ISO in man1


def test_lexicon_generator_output_is_reproducible_with_same_epoch(tmp_path: Path) -> None:
    """Two DIFFERENT epochs must produce different bytes; the same epoch must not.

    This is the counterfactual for the test above: if the timestamp were being ignored
    entirely, both assertions here would fail.
    """
    root = tmp_path / "w"
    root.mkdir()
    (root / "abraxas_ase").mkdir()
    (root / "abraxas_ase" / "tools").mkdir(parents=True)

    repo = Path(__file__).resolve().parents[1]
    shutil.copytree(repo / "lexicon_sources", root / "lexicon_sources")
    for rel in ("abraxas_ase/__init__.py", "abraxas_ase/tools/__init__.py", "abraxas_ase/tools/lexicon_update.py"):
        shutil.copy(repo / rel, root / rel)

    cmd = [
        sys.executable,
        "-m",
        "abraxas_ase.tools.lexicon_update",
        "--in",
        "lexicon_sources",
        "--out",
        "abraxas_ase",
    ]

    def _manifest_for(epoch: str) -> str:
        env = {**os.environ, "SOURCE_DATE_EPOCH": epoch}
        rc, out = _run(cmd, root, env)
        assert rc == 0, out
        return (root / "abraxas_ase" / "lexicon_manifest.json").read_text(encoding="utf-8")

    same = _manifest_for(SOURCE_DATE_EPOCH)
    assert _manifest_for(SOURCE_DATE_EPOCH) == same
    assert _manifest_for("1800000000") != same


def test_resolve_generated_at_utc(monkeypatch) -> None:
    from abraxas_ase.tools.lexicon_update import _resolve_generated_at_utc

    monkeypatch.setenv("SOURCE_DATE_EPOCH", SOURCE_DATE_EPOCH)
    assert _resolve_generated_at_utc() == PINNED_ISO

    # Unset -> wall clock, still a tz-aware UTC ISO-8601 stamp with microseconds dropped.
    monkeypatch.delenv("SOURCE_DATE_EPOCH")
    stamp = _resolve_generated_at_utc()
    parsed = dt.datetime.fromisoformat(stamp)
    assert parsed.tzinfo is not None
    assert parsed.microsecond == 0
    assert parsed.utcoffset() == dt.timedelta(0)
