from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)


def test_check_mode_detects_stale(tmp_path: Path) -> None:
    root = tmp_path / "w"
    root.mkdir()
    (root / "abraxas_ase").mkdir()
    (root / "abraxas_ase" / "tools").mkdir(parents=True)

    repo = Path(__file__).resolve().parents[1]
    shutil.copytree(repo / "lexicon_sources", root / "lexicon_sources")
    shutil.copy(repo / "abraxas_ase" / "__init__.py", root / "abraxas_ase" / "__init__.py")
    shutil.copy(repo / "abraxas_ase" / "tools" / "__init__.py", root / "abraxas_ase" / "tools" / "__init__.py")
    shutil.copy(repo / "abraxas_ase" / "tools" / "lexicon_update.py", root / "abraxas_ase" / "tools" / "lexicon_update.py")

    gen_cmd = ["python", "-m", "abraxas_ase.tools.lexicon_update", "--in", "lexicon_sources", "--out", "abraxas_ase"]
    rc, out = _run(gen_cmd, cwd=root)
    assert rc == 0, out

    # Check passes
    chk_cmd = gen_cmd + ["--check"]
    rc2, out2 = _run(chk_cmd, cwd=root)
    assert rc2 == 0, out2

    # Mutate sources: add one valid token
    sw = root / "lexicon_sources" / "subwords_core.txt"
    sw.write_text(sw.read_text(encoding="utf-8") + "\nwidget\n", encoding="utf-8")

    # Check should fail now
    rc3, out3 = _run(chk_cmd, cwd=root)
    assert rc3 != 0
    assert "stale" in out3.lower()
