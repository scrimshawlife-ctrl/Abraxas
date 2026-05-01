from __future__ import annotations

from copy import deepcopy

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.svg_ledger import build_ledger_run


def _manifest(render_id: str = "a" * 64, view_id: str = "v" * 64):
    return {
        "artifact": "AAL-VIZ-CANARY-SVG-RENDERER-001",
        "schema_version": "AALVizCanarySVGRenderManifest.v1",
        "render_id": render_id,
        "view_id": view_id,
        "svg_hash": "b" * 64,
        "view_packet_hash": "c" * 64,
        "dimensions": {"width": 1200, "height": 800},
        "counts": {"nodes": 1, "edges": 0, "alerts": 0, "actions": 0},
        "files": {"svg_path": "out/viz/test.svg"},
        "authority": {},
    }


def test_ledger_creation_and_dedupe_and_determinism():
    manifest = _manifest()
    m_before = deepcopy(manifest)
    run1 = build_ledger_run(manifest)
    assert run1["counts"]["entries_created"] == 1
    assert run1["counts"]["entries_existing"] == 0
    assert run1["counts"]["entries_total"] == 1

    entry = run1["entries"][0]
    expected_entry_id = sha256_hex(canonical_json({"render_id": manifest["render_id"], "svg_hash": manifest["svg_hash"], "view_packet_hash": manifest["view_packet_hash"]}))
    assert entry["entry_id"] == expected_entry_id
    assert entry["audit"]["render_manifest_hash"] == sha256_hex(canonical_json(manifest))
    assert entry["audit"]["lineage_hash"] == sha256_hex(canonical_json({"render_id": manifest["render_id"], "view_id": manifest["view_id"], "svg_hash": manifest["svg_hash"], "view_packet_hash": manifest["view_packet_hash"]}))

    run2 = build_ledger_run(manifest, previous=run1)
    assert run2["counts"]["entries_created"] == 0
    assert run2["counts"]["entries_existing"] == 1
    assert run2["entries"][0] == entry
    assert manifest == m_before


def test_ordering_authority_and_no_mutation():
    m1 = _manifest(render_id="f" * 64)
    m2 = _manifest(render_id="0" * 64)
    prior = build_ledger_run(m1)
    prior_before = deepcopy(prior)
    run = build_ledger_run(m2, previous=prior)

    assert [e["render_id"] for e in run["entries"]] == sorted([m1["render_id"], m2["render_id"]])
    assert canonical_json(run) == canonical_json(build_ledger_run(m2, previous=prior))

    auth = run["authority"]
    assert auth["svg_artifact_ledger_write"] is True
    for key in ("svg_rendering", "viz_projection", "inference", "production_activation", "baseline_mutation", "runtime_config_write", "promotion", "execution", "scheduler"):
        assert auth[key] is False

    assert prior == prior_before
