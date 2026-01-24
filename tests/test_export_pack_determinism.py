from __future__ import annotations

from pathlib import Path

from abraxas_ase.export_pack import build_export_pack


def _report() -> dict:
    return {
        "date": "2026-01-24",
        "version": "0.1.0",
        "schema_versions": {"ase_output": "v0.1"},
        "stats": {"items": 1, "tier2_hits": 2, "pfdi_alerts": 0},
        "key_fingerprint": "deadbeef",
        "run_id": "abcd1234",
        "high_tap_tokens": [
            {"token": "alpha", "tap": 1.2, "letter_entropy": 0.4, "length": 5, "unique_letters": 4},
            {"token": "beta", "tap": 0.8, "letter_entropy": 0.3, "length": 4, "unique_letters": 3},
        ],
        "verified_sub_anagrams": [
            {"sub": "war", "token": "alpha", "lane": "core", "source": "ap", "item_id": "x1"},
            {"sub": "peace", "token": "beta", "lane": "canary", "source": "ap", "item_id": "x2"},
        ],
        "sas": {
            "params": {"w_count": 1.0, "w_sources": 0.8, "w_events": 0.6, "w_len": 0.15, "max_len_bonus": 8},
            "rows": [
                {"sub": "war", "sas": 1.1, "mentions": 1, "sources_count": 1, "events_count": 1, "lane": "core"},
                {"sub": "peace", "sas": 0.9, "mentions": 1, "sources_count": 1, "events_count": 1, "lane": "canary"},
            ],
        },
    }


def _snapshot(dir_path: Path) -> dict:
    files = {}
    for path in sorted(dir_path.rglob("*")):
        if path.is_file():
            rel = path.relative_to(dir_path).as_posix()
            files[rel] = path.read_bytes()
    return files


def test_export_pack_determinism(tmp_path: Path) -> None:
    report = _report()
    out1 = tmp_path / "o1"
    out2 = tmp_path / "o2"

    build_export_pack(outdir=out1, report=report, tier="academic", safe_export=True, include_urls=False)
    build_export_pack(outdir=out2, report=report, tier="academic", safe_export=True, include_urls=False)

    pack1 = _snapshot(out1 / "pack_academic")
    pack2 = _snapshot(out2 / "pack_academic")
    assert pack1 == pack2
