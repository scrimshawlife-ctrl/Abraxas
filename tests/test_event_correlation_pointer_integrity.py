import json
from pathlib import Path

from abraxas.analysis.event_correlation.correlator import correlate, _json_pointer_get


FIX_DIR = Path("tests/fixtures/event_correlation/envelopes")


def _load_map():
    envs = {}
    for p in sorted(FIX_DIR.glob("*.json")):
        env = json.loads(p.read_text(encoding="utf-8"))
        aid = str(env.get("artifact_id") or env.get("id") or env.get("artifactId") or env.get("run_id") or p.name)
        envs[aid] = env
    return envs


def test_all_evidence_refs_resolve():
    env_map = _load_map()
    report = correlate(list(env_map.values()))

    for c in report.get("clusters", []):
        for ref in c.get("evidence_refs", []):
            aid = ref["artifact_id"]
            ptr = ref["pointer"]
            assert aid in env_map, f"missing artifact_id in fixtures: {aid}"
            _json_pointer_get(env_map[aid], ptr)

