"""Tests for canonical JSON encoding and hashing."""

from abraxas.core.canonical import canonical_json, sha256_hex


def test_canonical_json_deterministic():
    """Test that canonical_json produces stable output."""
    obj = {"b": 2, "a": 1, "c": [3, 2, 1]}

    # Multiple calls should produce identical output
    result1 = canonical_json(obj)
    result2 = canonical_json(obj)

    assert result1 == result2
    # Keys should be sorted
    assert result1 == '{"a":1,"b":2,"c":[3,2,1]}'


def test_canonical_json_key_ordering():
    """Test that keys are always sorted."""
    obj1 = {"z": 1, "a": 2, "m": 3}
    obj2 = {"a": 2, "m": 3, "z": 1}

    result1 = canonical_json(obj1)
    result2 = canonical_json(obj2)

    assert result1 == result2
    assert result1 == '{"a":2,"m":3,"z":1}'


def test_canonical_json_nested():
    """Test canonical JSON with nested objects."""
    obj = {
        "outer": {"inner_b": 2, "inner_a": 1},
        "list": [{"z": 1}, {"a": 2}],
    }

    result = canonical_json(obj)
    # Keys at all levels should be sorted
    assert '"inner_a":1,"inner_b":2' in result


def test_sha256_hex_string():
    """Test SHA256 hash of string."""
    text = "hello world"
    result = sha256_hex(text)

    # Known SHA256 hash of "hello world"
    expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert result == expected


def test_sha256_hex_bytes():
    """Test SHA256 hash of bytes."""
    data = b"hello world"
    result = sha256_hex(data)

    # Same as string version
    expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert result == expected


def test_sha256_hex_unicode():
    """Test SHA256 hash with unicode characters."""
    text = "hello 🌍"
    result = sha256_hex(text)

    # Should handle UTF-8 encoding properly
    assert len(result) == 64  # SHA256 produces 64 hex chars
    assert result == sha256_hex(text.encode("utf-8"))


def test_canonical_json_signature_stability():
    """Test that canonical JSON enables stable signatures."""
    data1 = {"key": "value", "number": 42}
    data2 = {"number": 42, "key": "value"}

    sig1 = sha256_hex(canonical_json(data1))
    sig2 = sha256_hex(canonical_json(data2))

    # Different input order should produce same signature
    assert sig1 == sig2
