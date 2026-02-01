from pathlib import Path

from abraxas.governance.inventory_report import build_inventory_report


def test_inventory_report_deterministic_output():
    repo_root = Path(__file__).parent.parent
    output_1 = build_inventory_report(repo_root=repo_root)
    output_2 = build_inventory_report(repo_root=repo_root)

    assert output_1 == output_2


def test_inventory_report_missing_paths(tmp_path):
    output = build_inventory_report(repo_root=tmp_path)

    assert "not_computable" in output
    assert "## Runes" in output
    assert "## Overlays" in output
    assert "## Canon metadata coverage" in output
