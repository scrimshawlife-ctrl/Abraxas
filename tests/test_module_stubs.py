from pathlib import Path


def test_module_stubs_exist() -> None:
    required = [
        "abraxas/oracle",
        "abraxas/scoring",
        "abraxas/canary",
    ]
    for path in required:
        module_path = Path(path)
        assert module_path.exists()
        assert (module_path / "__init__.py").exists()
        assert (module_path / "module_manifest.json").exists()
