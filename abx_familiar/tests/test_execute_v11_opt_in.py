from abx_familiar.ir.evidence_pack_v0 import EvidenceItem, EvidencePack
from abx_familiar.runtime.familiar_runtime import FamiliarRuntime


def test_execute_without_pack_keeps_none_output_hash():
    rt = FamiliarRuntime()
    out = rt.execute({"run_id": "legacy", "summoner": {"task_id": "t", "requested_ops": []}})
    assert out["ledger_entry"].output_hash is None
    assert out["ledger_entry"].not_computable is True


def test_execute_with_pack_uses_v11_prefix():
    pack = EvidencePack(
        pack_id="pack_exec_001",
        items=[EvidenceItem(evidence_id="e1", source_type="web", url="https://example.com")],
    )
    rt = FamiliarRuntime()
    out = rt.execute({"run_id": "optin", "pack": pack, "pack_ref": "memory"})
    assert out["binding"]["status"] == "BOUND_SHADOW"
    assert out["ledger_entry"]["meta"]["output_hash_method"] == "keep_output.v1"
    assert out["ledger_entry"]["output_hash"]
