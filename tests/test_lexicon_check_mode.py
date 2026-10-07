from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Pinned generation time (reproducible-builds convention).
#
# `lexicon_update` records when it ran (`generated_at_utc`) and hashes that value into
# `manifest_sha256`, which it then embeds in `lexicon_generated.py`. `--check` works by
# REGENERATING and comparing, so whenever the generate and the check land in different
# seconds the timestamps differ, the hashes differ, and `--check` reports STALE for output
# it wrote moments earlier.
#
# Measured, not assumed: between two generations of identical input the ONLY manifest key
# that differs is `generated_at_utc`; the merged token hashes are byte-identical. That is
# why this test passed alone (both calls inside one second) and failed inside the suite,
# where the gap between two subprocess rounds is larger and more variable.
#
# SOURCE_DATE_EPOCH pins the timestamp, so this test exercises staleness DETECTION instead
# of racing the clock. Sibling: tests/test_lexicon_generator_determinism.py.
SOURCE_DATE_EPOCH = "1700000000"

_ENV = {**os.environ, "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH}


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> tuple[int, str]:
    # sys.executable rather than a bare "python": a PATH lookup can resolve to a different
    # interpreter than the one running pytest.
    p = subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, env=env or _ENV
    )
    return p.returncode, (p.stdout + p.stderr)


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "w"
    root.mkdir()
    (root / "abraxas_ase").mkdir()
    (root / "abraxas_ase" / "tools").mkdir(parents=True)

    repo = Path(__file__).resolve().parents[1]
    shutil.copytree(repo / "lexicon_sources", root / "lexicon_sources")
    shutil.copy(repo / "abraxas_ase" / "__init__.py", root / "abraxas_ase" / "__init__.py")
    shutil.copy(repo / "abraxas_ase" / "tools" / "__init__.py", root / "abraxas_ase" / "tools" / "__init__.py")
    shutil.copy(repo / "abraxas_ase" / "tools" / "lexicon_update.py", root / "abraxas_ase" / "tools" / "lexicon_update.py")
    return root


def _gen_cmd() -> list[str]:
    return [
        sys.executable,
        "-m",
        "abraxas_ase.tools.lexicon_update",
        "--in",
        "lexicon_sources",
        "--out",
        "abraxas_ase",
    ]


def test_check_mode_detects_stale(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    gen_cmd = _gen_cmd()

    rc, out = _run(gen_cmd, root)
    assert rc == 0, out

    # Check passes: nothing changed since generation.
    rc2, out2 = _run(gen_cmd + ["--check"], root)
    assert rc2 == 0, out2

    # Mutate sources: add one valid token.
    sw = root / "lexicon_sources" / "subwords_core.txt"
    sw.write_text(sw.read_text(encoding="utf-8") + "\nwidget\n", encoding="utf-8")

    # Check should fail now, and say why.
    rc3, out3 = _run(gen_cmd + ["--check"], root)
    assert rc3 != 0
    assert "stale" in out3.lower()


def test_check_is_not_racing_the_clock(tmp_path: Path) -> None:
    """The counterfactual for the pin: `--check` must not depend on elapsed time.

    Without a pinned timestamp this fails, and it fails for the wrong reason — regenerating
    produces a different `generated_at_utc`, so the comparison reports stale on identical
    content. Deliberately running generation and check with a gap in between (which is what
    the suite does) is the condition that exposed the flake, so it is asserted directly.
    """
    import time

    root = _workspace(tmp_path)
    gen_cmd = _gen_cmd()

    rc, out = _run(gen_cmd, root)
    assert rc == 0, out

    time.sleep(1.2)  # straddle a second boundary on purpose

    rc2, out2 = _run(gen_cmd + ["--check"], root)
    assert rc2 == 0, (
        "--check reported stale on unmodified content after 1.2s. The generation timestamp "
        "is leaking into the comparison.\n" + out2
    )


def test_check_still_detects_stale_when_the_pinned_time_changes(tmp_path: Path) -> None:
    """Pinning must not make `--check` blind: a different generation time is a real
    difference, and the check must still see it. This is what stops the pin from being a
    way of switching the guardrail off."""
    root = _workspace(tmp_path)
    gen_cmd = _gen_cmd()

    rc, out = _run(gen_cmd, root)
    assert rc == 0, out

    other_env = {**os.environ, "SOURCE_DATE_EPOCH": "1800000000"}
    rc2, out2 = _run(gen_cmd + ["--check"], root, env=other_env)
    assert rc2 != 0, (
        "--check passed despite being regenerated with a different SOURCE_DATE_EPOCH, so "
        "it is no longer comparing anything meaningful"
    )
    assert "stale" in out2.lower()
