from pathlib import Path

from abraxas.governance.rune_registry_gate import run_gate


def _write_catalog(root: Path, rune_ids: list[str]) -> Path:
    catalog_dir = root / "abraxas_ase" / "runes"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = catalog_dir / "catalog.v0.yaml"
    lines = [
        'catalog_version: "0.1.0"',
        'schema_version: "catalog.v0"',
        "runes:",
    ]
    for rune_id in rune_ids:
        lines.extend(
            [
                f"  - rune_id: {rune_id}",
                "    module: abraxas_ase.runes.stub",
                "    handler: run",
                "    version: \"1.0.0\"",
                f"    domain_id: {rune_id}",
                "    input_schema: sdct/contracts/sdct_domain_params.v0.schema.json",
                "    output_schema: sdct/contracts/sdct_evidence_row.v0.schema.json",
                "    tier_allowed:",
                "      - psychonaut",
                "      - academic",
                "      - enterprise",
                "    description: \"stub\"",
                "    constraints:",
                "      - deterministic",
                "      - provenance_required",
            ]
        )
    catalog_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return catalog_path


def _write_rune_module(root: Path, file_name: str, rune_id: str) -> Path:
    runes_dir = root / "abraxas_ase" / "runes"
    runes_dir.mkdir(parents=True, exist_ok=True)
    module_path = runes_dir / file_name
    module_path.write_text(
        "\n".join(
            [
                '"""ABX-Runes Adapter: {rune_id}"""'.format(rune_id=rune_id),
                "def run(payload, ctx):",
                f'    return {{"rune_id": "{rune_id}"}}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return module_path


def test_rune_registry_gate_deterministic_output(tmp_path):
    _write_catalog(tmp_path, ["sdct.text_subword.v1", "sdct.digit_motif.v1"])
    _write_rune_module(tmp_path, "sdct_text_subword_v1.py", "sdct.text_subword.v1")
    _write_rune_module(tmp_path, "sdct_digit_motif_v1.py", "sdct.digit_motif.v1")

    exit_code_1, output_1 = run_gate(repo_root=tmp_path)
    exit_code_2, output_2 = run_gate(repo_root=tmp_path)

    assert exit_code_1 == 0
    assert exit_code_2 == 0
    assert output_1 == output_2


def test_rune_registry_gate_failures_emit_scaffold(tmp_path):
    _write_catalog(tmp_path, ["sdct.text_subword.v1"])
    _write_rune_module(tmp_path, "sdct_text_subword_v1.py", "sdct.text_subword.v1")
    _write_rune_module(tmp_path, "sdct_fake_v1.py", "sdct.fake.v1")

    exit_code, output = run_gate(repo_root=tmp_path)

    assert exit_code != 0
    assert "SCaffold Pack" in output
    assert "sdct.fake.v1" in output
    assert "handler: run" in output


def test_rune_registry_gate_pass(tmp_path):
    _write_catalog(tmp_path, ["sdct.text_subword.v1"])
    _write_rune_module(tmp_path, "sdct_text_subword_v1.py", "sdct.text_subword.v1")

    exit_code, output = run_gate(repo_root=tmp_path)

    assert exit_code == 0
    assert "status: PASS" in output
