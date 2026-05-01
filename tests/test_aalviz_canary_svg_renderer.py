from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from abraxas.viz.svg_runner import build_outputs, run_renderer


def _packet():
    return {
        "view_id": "view_abc123",
        "nodes": [
            {"node_id": "n1", "state": "healthy", "position": [-1, 1], "color": "cyan"},
            {"node_id": "n2", "state": "<script>", "position": [1, -1], "color": "unknown"},
        ],
        "edges": [{"source": "n1", "target": "n2", "edge_type": "depends"}],
        "alerts": [
            {"severity": "warning", "message": "first"},
            {"severity": "critical", "message": "second"},
        ],
        "actions": [
            {"priority": "low", "label": "a1"},
            {"priority": "high", "label": "a2"},
        ],
    }


def test_svg_renderer_deterministic(tmp_path: Path):
    packet = _packet()
    before = deepcopy(packet)
    out1 = build_outputs(packet, "out.svg")
    out2 = build_outputs(packet, "out.svg")

    assert out1.svg.startswith("<svg")
    assert 'id="node-n1"' in out1.svg
    assert 'id="edge-n1-n2-depends"' in out1.svg
    assert out1.svg.index("first") < out1.svg.index("second")
    assert out1.svg.index("a1") < out1.svg.index("a2")
    assert out1.manifest["view_packet_hash"][:12] in out1.svg
    assert out1.manifest["svg_hash"] == out2.manifest["svg_hash"]
    assert out1.manifest["render_id"] == out2.manifest["render_id"]
    assert "<script>" not in out1.svg
    assert "&lt;script&gt;" in out1.svg
    assert packet == before
    assert out1.manifest["counts"] == {"nodes": 2, "edges": 1, "alerts": 2, "actions": 2}

    authority = out1.manifest["authority"]
    assert authority["inference"] is False
    assert authority["production_activation"] is False
    assert authority["baseline_mutation"] is False
    assert authority["runtime_config_write"] is False
    assert authority["promotion"] is False
    assert authority["execution"] is False
    assert authority["scheduler"] is False


def test_cli_output_byte_identical(tmp_path: Path):
    packet_path = tmp_path / "view.json"
    packet_path.write_text(json.dumps(_packet()), encoding="utf-8")

    svg_out = tmp_path / "stable.svg"
    man_out = tmp_path / "stable.json"

    run_renderer(packet_path, svg_out, man_out)
    first_svg = svg_out.read_bytes()
    first_manifest = man_out.read_bytes()
    run_renderer(packet_path, svg_out, man_out)

    assert first_svg == svg_out.read_bytes()
    assert first_manifest == man_out.read_bytes()
