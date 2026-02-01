from pathlib import Path
import re

from abraxas.governance.rune_registry_gate import run_gate


def _module_for_rune_id(rune_id: str) -> str:
    match = re.match(r"^sdct\.(?P<name>[a-z0-9_]+)\.v(?P<major>\d+)$", rune_id)
    if not match:
        return "abraxas_ase.runes.unknown"
    name = match.group("name")
    major = match.group("major")
    return f"abraxas_ase.runes.sdct_{name}_v{major}"


def _write_catalog(root: Path, rune_ids: list[str], module_overrides: dict[str, str] | None = None) -> Path:
    catalog_dir = root / "abraxas_ase" / "runes"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = catalog_dir / "catalog.v0.yaml"
    module_overrides = module_overrides or {}
    lines = [
        'catalog_version: "0.1.0"',
        'schema_version: "catalog.v0"',
        "runes:",
    ]
    for rune_id in rune_ids:
        module_path = module_overrides.get(rune_id, _module_for_rune_id(rune_id))
        lines.extend(
            [
                f"  - rune_id: {rune_id}",
                f"    module: {module_path}",
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


def _write_rune_module(root: Path, rune_id: str) -> Path:
    runes_dir = root / "abraxas_ase" / "runes"
    runes_dir.mkdir(parents=True, exist_ok=True)
    file_name = _module_for_rune_id(rune_id).split(".")[-1] + ".py"
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
    _write_rune_module(tmp_path, "sdct.text_subword.v1")
    _write_rune_module(tmp_path, "sdct.digit_motif.v1")

    exit_code_1, output_1 = run_gate(repo_root=tmp_path)
    exit_code_2, output_2 = run_gate(repo_root=tmp_path)

    assert exit_code_1 == 0
    assert exit_code_2 == 0
    assert output_1 == output_2


def test_rune_registry_gate_failures_emit_scaffold(tmp_path):
    _write_catalog(tmp_path, ["sdct.text_subword.v1"])
    _write_rune_module(tmp_path, "sdct.text_subword.v1")
    _write_rune_module(tmp_path, "sdct.fake.v1")

    exit_code, output = run_gate(repo_root=tmp_path)

    assert exit_code != 0
    assert "SCaffold Pack" in output
    assert "sdct.fake.v1" in output
    assert "handler: run" in output


def test_rune_registry_gate_broken_module_target(tmp_path):
    _write_catalog(
        tmp_path,
        ["sdct.text_subword.v1"],
        module_overrides={"sdct.text_subword.v1": "abraxas_ase.runes.sdct_missing_v1"},
    )

    exit_code, output = run_gate(repo_root=tmp_path)

    assert exit_code == 3
    assert "Broken module targets" in output


def test_rune_registry_gate_pass(tmp_path):
    _write_catalog(tmp_path, ["sdct.text_subword.v1"])
    _write_rune_module(tmp_path, "sdct.text_subword.v1")

    exit_code, output = run_gate(repo_root=tmp_path)

    assert exit_code == 0
    assert "status: PASS" in output
