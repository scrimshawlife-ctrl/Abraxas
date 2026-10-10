# tests/test_aether_no_consumer.py
import pytest

def test_no_consumer_of_multimodal_integration():
    # This test documents the UNKNOWN. It will fail (or be updated) when a consumer appears.
    import subprocess
    result = subprocess.run(
        ["grep", "-r", "MULTIMODAL_INTEGRATION", "--include=*.py", "."],
        capture_output=True, text=True, cwd="."
    )
    # Exclude non-consumer references: contract, aether provider, manifest (declaration),
    # production.py (legacy mock), and build artifacts.
    lines = [l for l in result.stdout.splitlines()
             if "contract.py" not in l
             and "aether" not in l
             and "manifest.py" not in l
             and "production.py" not in l
             and "/build/" not in l]
    assert len(lines) == 0, f"Unexpected consumers found: {lines}"