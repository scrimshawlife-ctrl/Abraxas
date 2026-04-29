from __future__ import annotations

from typing import Any, Mapping

from abx.proof.artifact_writer import sha256_for_obj, write_json_artifact


def validate_patch004_receipt_for_binding(receipt: Mapping[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if receipt.get("sandbox_only") is not True:
        reasons.append("sandbox_only_false")
    if int(receipt.get("actions_executed", 0) or 0) != 0:
        reasons.append("actions_executed_nonzero")
    files_modified = receipt.get("files_modified", [])
    if isinstance(files_modified, list) and len(files_modified) > 0:
        reasons.append("files_modified_nonempty")
    if bool(receipt.get("execution_triggered", False)):
        reasons.append("execution_triggered_true")
    if bool(receipt.get("runtime_mutation", False)):
        reasons.append("runtime_mutation_true")
    if bool(receipt.get("authority_leak_detected", False)):
        reasons.append("authority_leak_detected_true")
    if bool(receipt.get("patch_004_execution_allowed", False)):
        reasons.append("patch_execution_allowed_true")
    return (len(reasons) == 0, reasons)


def build_patch004_receipt_binding(receipt: Mapping[str, Any], manifest: Mapping[str, Any] | None = None, artifact_meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    ok, reasons = validate_patch004_receipt_for_binding(receipt)
    run_id = str(receipt.get("run_id", "NOT_COMPUTABLE") or "NOT_COMPUTABLE")
    manifest_id = str(receipt.get("manifest_id", "NOT_COMPUTABLE") or "NOT_COMPUTABLE")
    if manifest is not None:
        manifest_id = str(manifest.get("manifest_id", manifest_id) or manifest_id)
    receipt_sha = "NOT_COMPUTABLE"
    manifest_sha = "NOT_COMPUTABLE"
    if artifact_meta and isinstance(artifact_meta, Mapping):
        receipt_sha = str(artifact_meta.get("receipt_sha256", receipt_sha))
        manifest_sha = str(artifact_meta.get("manifest_sha256", manifest_sha))
    elif ok:
        receipt_sha = sha256_for_obj(dict(receipt))
        if manifest is not None:
            manifest_sha = sha256_for_obj(dict(manifest))

    status = "BOUND" if ok else ("NOT_COMPUTABLE" if "sandbox_only_false" in reasons else "BLOCKED")
    return {
        "schema_version": "Patch004ReceiptBinding.v1",
        "binding_id": f"patch004-binding-{run_id}",
        "source_run_id": run_id,
        "source_manifest_id": manifest_id,
        "receipt_sha256": receipt_sha,
        "manifest_sha256": manifest_sha,
        "sandbox_only": bool(receipt.get("sandbox_only", False)),
        "execution_allowed": False,
        "runtime_mutation_allowed": False,
        "actions_executed": int(receipt.get("actions_executed", 0) or 0),
        "files_modified": list(receipt.get("files_modified", [])) if isinstance(receipt.get("files_modified", []), list) else [],
        "authority_leak_detected": bool(receipt.get("authority_leak_detected", False)),
        "binding_status": status,
    }


def write_patch004_binding_artifacts(run_id: str, manifest: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    base = f"out/repair/patch004/{run_id}/"
    manifest_path = base + "manifest.json"
    receipt_path = base + "receipt.json"
    manifest_sha = write_json_artifact(dict(manifest), manifest_path)
    receipt_sha = write_json_artifact(dict(receipt), receipt_path)
    binding = build_patch004_receipt_binding(
        receipt,
        manifest=manifest,
        artifact_meta={"manifest_sha256": manifest_sha, "receipt_sha256": receipt_sha},
    )
    binding_path = base + "binding.json"
    binding_sha = write_json_artifact(binding, binding_path)
    return {
        "manifest_path": manifest_path,
        "receipt_path": receipt_path,
        "binding_path": binding_path,
        "manifest_sha256": manifest_sha,
        "receipt_sha256": receipt_sha,
        "binding_sha256": binding_sha,
        "binding": binding,
    }
