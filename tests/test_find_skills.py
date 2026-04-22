from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from abraxas.runes.find_skills import find_skills


BASE_INPUT = {
    "query": "find skills deterministic",
    "domains": ["discovery"],
    "capabilities": ["find", "registry"],
    "limit": 10,
    "include_shadow": False,
    "sources": ["aal_core/runes/catalog.v0.yaml"],
}


def _write_registry(path: Path, runes: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"schema_version": "aal.runes.catalog.v0", "runes": runes}, sort_keys=False), encoding="utf-8")


def _write_schemas(root: Path) -> None:
    schemas_dir = root / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    src_in = Path("schemas/FindSkillsInput.v1.json")
    src_out = Path("schemas/FindSkillsOutput.v1.json")
    (schemas_dir / "FindSkillsInput.v1.json").write_text(src_in.read_text(encoding="utf-8"), encoding="utf-8")
    (schemas_dir / "FindSkillsOutput.v1.json").write_text(src_out.read_text(encoding="utf-8"), encoding="utf-8")


def _setup(root: Path, runes: list[dict]) -> None:
    _write_schemas(root)
    _write_registry(root / "aal_core/runes/catalog.v0.yaml", runes)


def _rune(
    rune_id: str,
    name: str,
    description: str,
    domains: list[str],
    capabilities: list[str],
    version: str = "v1",
) -> dict:
    return {
        "rune_id": rune_id,
        "id": rune_id,
        "name": name,
        "description": description,
        "domains": domains,
        "capabilities": capabilities,
        "version": version,
        "input_schema": "schemas/FindSkillsInput.v1.json",
        "output_schema": "schemas/FindSkillsOutput.v1.json",
    }


def test_same_input_identical_output(tmp_path: Path) -> None:
    _setup(
        tmp_path,
        [
            _rune("RUNE.FIND_SKILLS", "Find Skills", "Deterministic skill discovery", ["discovery"], ["find", "registry"]),
        ],
    )
    first = find_skills(BASE_INPUT, base_path=tmp_path)
    second = find_skills(BASE_INPUT, base_path=tmp_path)
    assert first == second


def test_missing_registry_not_computable(tmp_path: Path) -> None:
    _write_schemas(tmp_path)
    result = find_skills(BASE_INPUT, base_path=tmp_path)
    assert result["status"] == "NOT_COMPUTABLE"


def test_empty_query_not_computable(tmp_path: Path) -> None:
    _setup(tmp_path, [_rune("RUNE.FIND_SKILLS", "Find Skills", "Deterministic", ["discovery"], ["find"])])
    payload = {**BASE_INPUT, "query": "   "}
    result = find_skills(payload, base_path=tmp_path)
    assert result["status"] == "NOT_COMPUTABLE"


def test_ranking_stability_and_tiebreak(tmp_path: Path) -> None:
    _setup(
        tmp_path,
        [
            _rune("RUNE.B", "Find Skills", "deterministic finder", ["discovery"], ["find", "registry"]),
            _rune("RUNE.A", "Find Skills", "deterministic finder", ["discovery"], ["find", "registry"]),
        ],
    )
    result = find_skills(BASE_INPUT, base_path=tmp_path)
    assert result["status"] == "OK"
    assert [m["skill_id"] for m in result["matches"]] == ["RUNE.A", "RUNE.B"]


def test_hash_consistency(tmp_path: Path) -> None:
    _setup(
        tmp_path,
        [_rune("RUNE.FIND_SKILLS", "Find Skills", "Deterministic skill discovery", ["discovery"], ["find", "registry"])],
    )
    first = find_skills(BASE_INPUT, base_path=tmp_path)
    second = find_skills(BASE_INPUT, base_path=tmp_path)
    assert first["query_hash"] == second["query_hash"]
    assert first["matches"][0]["provenance"]["hash"] == second["matches"][0]["provenance"]["hash"]


def test_duplicate_skill_detection(tmp_path: Path) -> None:
    _setup(
        tmp_path,
        [
            _rune("RUNE.FIND_SKILLS", "Find Skills", "Deterministic", ["discovery"], ["find"]),
            _rune("RUNE.FIND_SKILLS", "Find Skills", "Deterministic", ["discovery"], ["find"]),
        ],
    )
    result = find_skills(BASE_INPUT, base_path=tmp_path)
    assert result["shadow_summary"]["duplicate_skill_ids"]


def test_missing_metadata_detection(tmp_path: Path) -> None:
    _setup(
        tmp_path,
        [
            {
                "rune_id": "RUNE.X",
                "id": "RUNE.X",
                "name": "",
                "description": "",
                "domains": [],
                "capabilities": [],
            }
        ],
    )
    result = find_skills(BASE_INPUT, base_path=tmp_path)
    assert result["shadow_summary"]["missing_metadata"]


def test_schema_existence_validation(tmp_path: Path) -> None:
    _setup(
        tmp_path,
        [
            {
                "rune_id": "RUNE.FIND_SKILLS",
                "id": "RUNE.FIND_SKILLS",
                "name": "Find Skills",
                "description": "Deterministic skill discovery",
                "domains": ["discovery"],
                "capabilities": ["find"],
                "input_schema": "schemas/does_not_exist.json",
                "output_schema": "schemas/also_missing.json",
            }
        ],
    )
    result = find_skills(BASE_INPUT, base_path=tmp_path)
    assert result["shadow_summary"]["missing_schema_refs"]


def test_12_run_invariance(tmp_path: Path) -> None:
    _setup(
        tmp_path,
        [_rune("RUNE.FIND_SKILLS", "Find Skills", "Deterministic skill discovery", ["discovery"], ["find", "registry"])],
    )
    baseline = find_skills(BASE_INPUT, base_path=tmp_path)
    for _ in range(11):
        assert find_skills(BASE_INPUT, base_path=tmp_path) == baseline


def test_malformed_registry_payload_not_computable(tmp_path: Path) -> None:
    _write_schemas(tmp_path)
    registry = tmp_path / "aal_core/runes/catalog.v0.yaml"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text("schema_version: aal.runes.catalog.v0\nrunes: invalid\n", encoding="utf-8")
    result = find_skills(BASE_INPUT, base_path=tmp_path)
    assert result["status"] == "NOT_COMPUTABLE"


def test_match_provenance_fields_present(tmp_path: Path) -> None:
    _setup(
        tmp_path,
        [_rune("RUNE.FIND_SKILLS", "Find Skills", "Deterministic skill discovery", ["discovery"], ["find", "registry"])],
    )
    result = find_skills(BASE_INPUT, base_path=tmp_path)
    match = result["matches"][0]
    assert match["provenance"]["registry_path"] == "aal_core/runes/catalog.v0.yaml"
    assert len(match["provenance"]["hash"]) == 64
