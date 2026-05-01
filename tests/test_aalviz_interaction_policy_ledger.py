from pathlib import Path

from abraxas.core.canonical import canonical_json
from abraxas.viz.interaction_policy_ledger import build_ledger
from abraxas.viz.interaction_policy_ledger_runner import run


def _policy():
    return {
        "policy_id": "a" * 64,
        "policy_hash": "b" * 64,
        "allowed_future_interactions": ["node_hover"],
        "forbidden_interactions": ["animation_loop"],
        "authority": {"interaction_runtime": False},
    }


def _manifest():
    return {
        "manifest_hash": "c" * 64,
        "files": {"package-lock.json": "d" * 64},
    }


def test_no_duplicates_and_determinism(tmp_path: Path):
    policy = _policy()
    manifest = _manifest()
    run1 = build_ledger(policy, manifest)
    run2 = build_ledger(policy, manifest, run1)
    assert len(run1["entries"]) == len(run2["entries"])
    assert canonical_json(run1) == canonical_json(build_ledger(policy, manifest))

    p = tmp_path / "policy.json"
    m = tmp_path / "manifest.json"
    o = tmp_path / "out.json"
    p.write_text(canonical_json(policy), encoding="utf-8")
    m.write_text(canonical_json(manifest), encoding="utf-8")
    run(p, m, o)
    first = o.read_bytes()
    run(p, m, o)
    assert first == o.read_bytes()
