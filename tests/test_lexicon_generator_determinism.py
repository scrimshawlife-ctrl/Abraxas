from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)


def test_lexicon_generator_is_deterministic(tmp_path: Path) -> None:
    # Arrange: copy minimal repo structure into temp
    root = tmp_path / "w"
    root.mkdir()
    (root / "abraxas_ase").mkdir()
    (root / "abraxas_ase" / "tools").mkdir(parents=True)

    # Copy the tool into temp workspace (assumes test runs in real repo)
    # If you run tests in-repo, you can simplify this to import and call main().
    # Here we do module invocation to match real behavior.
    repo = Path(__file__).resolve().parents[1]
    shutil.copytree(repo / "lexicon_sources", root / "lexicon_sources")
    shutil.copy(repo / "abraxas_ase" / "__init__.py", root / "abraxas_ase" / "__init__.py")
    shutil.copy(repo / "abraxas_ase" / "tools" / "__init__.py", root / "abraxas_ase" / "tools" / "__init__.py")
    shutil.copy(repo / "abraxas_ase" / "tools" / "lexicon_update.py", root / "abraxas_ase" / "tools" / "lexicon_update.py")

    # Run twice
    cmd = ["python", "-m", "abraxas_ase.tools.lexicon_update", "--in", "lexicon_sources", "--out", "abraxas_ase"]
    rc1, out1 = _run(cmd, cwd=root)
    assert rc1 == 0, out1
    gen1 = (root / "abraxas_ase" / "lexicon_generated.py").read_text(encoding="utf-8")
    man1 = (root / "abraxas_ase" / "lexicon_manifest.json").read_text(encoding="utf-8")

    rc2, out2 = _run(cmd, cwd=root)
    assert rc2 == 0, out2
    gen2 = (root / "abraxas_ase" / "lexicon_generated.py").read_text(encoding="utf-8")
    man2 = (root / "abraxas_ase" / "lexicon_manifest.json").read_text(encoding="utf-8")

    assert gen1 == gen2
    assert man1 == man2
