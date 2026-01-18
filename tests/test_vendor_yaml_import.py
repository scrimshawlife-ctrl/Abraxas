"""Tests for vendored PyYAML import shim."""

from __future__ import annotations


def test_yaml_import_and_parse():
    import yaml

    assert yaml.safe_load("a: 1") == {"a": 1}


def test_yaml_vendor_path():
    import yaml

    assert "/vendor/pyyaml/" in yaml.__file__.replace("\\", "/")
