from pathlib import Path

from abraxas.governance import rune_registry_gate
from abraxas.governance.inventory_report import build_inventory_report, run_inventory_report


def _write_catalog(root: Path, rune_ids: list[str], catalog_rel: Path) -> None:
    catalog_dir = root / catalog_rel.parent
    catalog_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = root / catalog_rel
    lines = [
        'catalog_version: "0.1.0"',
        'schema_version: "catalog.v0"',
        "runes:",
    ]
    for rune_id in rune_ids:
        lines.extend(
            [
                f"  - rune_id: {rune_id}",
                f"    module: abraxas_ase.runes.sdct_{rune_id.split('.', 1)[1].replace('.', '_')}",
            ]
        )
    catalog_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_rune_module(root: Path, rune_id: str, runes_rel: Path) -> None:
    runes_dir = root / runes_rel
    runes_dir.mkdir(parents=True, exist_ok=True)
    file_name = "sdct_" + rune_id.split(".", 1)[1].replace(".", "_") + ".py"
    module_path = runes_dir / file_name
    module_path.write_text(
        "\n".join(
            [
                f'"""ABX-Runes Adapter: {rune_id}"""',
                "def run(payload, ctx):",
                f'    return {{"rune_id": "{rune_id}"}}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_inventory_report_deterministic_output(tmp_path, monkeypatch):
    catalog_rel = Path("catalogs") / "catalog.v0.yaml"
    runes_rel = Path("runes")
    monkeypatch.setattr(rune_registry_gate, "CATALOG_PATH", catalog_rel)
    monkeypatch.setattr(rune_registry_gate, "DISCOVERY_ROOT", runes_rel)

    _write_catalog(tmp_path, ["sdct.text_subword.v1", "sdct.digit_motif.v1"], catalog_rel)
    _write_rune_module(tmp_path, "sdct.text_subword.v1", runes_rel)
    _write_rune_module(tmp_path, "sdct.digit_motif.v1", runes_rel)

    output_1 = build_inventory_report(repo_root=tmp_path)
    output_2 = build_inventory_report(repo_root=tmp_path)

    assert output_1 == output_2


def test_inventory_report_empty_repo(tmp_path, monkeypatch):
    catalog_rel = Path("catalogs") / "catalog.v0.yaml"
    runes_rel = Path("runes")
    monkeypatch.setattr(rune_registry_gate, "CATALOG_PATH", catalog_rel)
    monkeypatch.setattr(rune_registry_gate, "DISCOVERY_ROOT", runes_rel)

    exit_code, output = run_inventory_report(repo_root=tmp_path)

    assert exit_code == 1
    assert "not_computable" in output
    assert "## Implemented Runes (code)" in output


def test_inventory_report_stable_ordering(tmp_path, monkeypatch):
    catalog_rel = Path("catalogs") / "catalog.v0.yaml"
    runes_rel = Path("runes")
    monkeypatch.setattr(rune_registry_gate, "CATALOG_PATH", catalog_rel)
    monkeypatch.setattr(rune_registry_gate, "DISCOVERY_ROOT", runes_rel)

    _write_catalog(tmp_path, ["sdct.text_subword.v1", "sdct.digit_motif.v1"], catalog_rel)
    _write_rune_module(tmp_path, "sdct.digit_motif.v1", runes_rel)
    _write_rune_module(tmp_path, "sdct.text_subword.v1", runes_rel)

    output = build_inventory_report(repo_root=tmp_path)
    lines = output.splitlines()
    start = lines.index("## Implemented Runes (code)") + 1
    end = lines.index("## Registered Runes (catalog)")
    rune_lines = [line for line in lines[start:end] if line.startswith("- ")]

    assert "sdct.digit_motif.v1" in rune_lines[0]
    assert "sdct.text_subword.v1" in rune_lines[1]
