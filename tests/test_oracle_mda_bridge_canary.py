import json

from abraxas.mda.registry import DomainRegistryV1
from abraxas.mda.types import MDARunEnvelope
from abraxas.mda.run import run_mda
from abraxas.mda.signal_layer_v2 import mda_to_oracle_signal_v2, shallow_schema_check
from abraxas.oracle.mda_bridge import run_mda_for_oracle
from abraxas.mda.adapters.router import AdapterRouter


def _load(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_oracle_bridge_matches_direct_run_slice_hash_evidence_bundle():
    reg = DomainRegistryV1()
    bundle = _load("abraxas/mda/fixtures/evidence_bundle_sample.json")

    domains = ("tech_ai", "culture_memes")
    subdomains = ("tech_ai:foundation_models", "culture_memes:slang_language_drift")

    # Oracle bridge path
    out_bridge = run_mda_for_oracle(
        env="sandbox",
        run_at_iso="2026-01-01T00:00:00Z",
        seed=1337,
        abraxas_version="2.2.0",
        domains=domains,
        subdomains=subdomains,
        payload=bundle,
    )
    sig_bridge = mda_to_oracle_signal_v2(out_bridge)
    shallow_schema_check(sig_bridge)
    h_bridge = sig_bridge["oracle_signal_v2"]["meta"]["slice_hash"]

    # Direct run path (CLI-equivalent without filesystem)
    router = AdapterRouter()
    adapted = router.adapt(bundle, registry=reg)
    inputs = {"vectors": adapted.vectors, "adapter_notes": adapted.notes}

    env = MDARunEnvelope(
        env="sandbox",
        run_at_iso="2026-01-01T00:00:00Z",
        seed=1337,
        promotion_enabled=False,
        enabled_domains=domains,
        enabled_subdomains=subdomains,
        inputs=inputs,
    )
    _, out_direct = run_mda(env, abraxas_version="2.2.0", registry=reg)
    sig_direct = mda_to_oracle_signal_v2(out_direct)
    shallow_schema_check(sig_direct)
    h_direct = sig_direct["oracle_signal_v2"]["meta"]["slice_hash"]

    assert h_bridge == h_direct


def test_oracle_bridge_vectors_only_adapter_path_produces_valid_signal():
    reg = DomainRegistryV1()
    vec_only = _load("abraxas/mda/fixtures/vectors_only_sample.json")

    out_bridge = run_mda_for_oracle(
        env="sandbox",
        run_at_iso="2026-01-01T00:00:00Z",
        seed=1337,
        abraxas_version="2.2.0",
        domains=("tech_ai",),
        subdomains=("tech_ai:foundation_models",),
        payload=vec_only,
    )
    sig = mda_to_oracle_signal_v2(out_bridge)
    shallow_schema_check(sig)
    assert sig["oracle_signal_v2"]["meta"]["slice_hash"]

