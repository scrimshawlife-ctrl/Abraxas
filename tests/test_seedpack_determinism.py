"""Tests for deterministic seedpack generation."""

from __future__ import annotations

import hashlib

from abraxas.seeds.year_seed_2025 import write_seedpack


def _file_hash(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_seedpack_generator_deterministic(tmp_path):
    path1 = tmp_path / "seedpack1.json"
    path2 = tmp_path / "seedpack2.json"

    write_seedpack(path1)
    write_seedpack(path2)

    assert _file_hash(path1) == _file_hash(path2), "Seedpack output must be deterministic"
