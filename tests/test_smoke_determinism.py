"""Test determinism of smoke test pipeline.

Ensures that running the pipeline with the same input produces identical output.
"""

from abx.core.pipeline import run_oracle

def test_smoke_is_deterministic():
    """Verify pipeline produces identical output for same input."""
    inp = {"intent": "smoke", "v": 1}
    a = run_oracle(inp)
    b = run_oracle(inp)
    assert a == b, "Pipeline must be deterministic for same input"

def test_smoke_stable_output():
    """Verify smoke test produces expected stable structure."""
    inp = {"intent": "smoke", "v": 1}
    out = run_oracle(inp)

    assert "oracle_vector" in out
    assert "semiotic_weather" in out
    assert "outputs" in out
    assert out["oracle_vector"] == inp

if __name__ == "__main__":
    # Allow running directly without pytest
    import sys

    try:
        test_smoke_is_deterministic()
        print("✓ test_smoke_is_deterministic passed")
    except AssertionError as e:
        print(f"✗ test_smoke_is_deterministic failed: {e}")
        sys.exit(1)

    try:
        test_smoke_stable_output()
        print("✓ test_smoke_stable_output passed")
    except AssertionError as e:
        print(f"✗ test_smoke_stable_output failed: {e}")
        sys.exit(1)

    print("\nAll tests passed!")
