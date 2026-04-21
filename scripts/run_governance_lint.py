#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path


CANONICAL_COMMAND_MARKERS = [
    "proof-run",
    "promotion-check",
    "promotion-policy",
    "scripts/run_execution_attestation.py",
    "run_release_readiness.py",
    "ts-canonical-check",
    "/api/operator/run/:runId",
    "/api/operator/compare/:runA/:runB",
    "/api/operator/release-readiness/:runId",
    "/api/operator/evidence/:runId",
    "/runs/{run_id}/console",
    "/runs/{run_id}/evidence",
    "/runs/compare",
    "/release/readiness",
]

REQUIRED_TIER_MARKERS = ["Tier 1", "Tier 2", "Tier 2.5", "Tier 2.75", "Tier 3"]

HEAVY_SCRIPT_PATTERN = re.compile(r"(acceptance|attestation|promotion|seal|execution)")

CLASSIFIED_PATHS = {
    "scripts/run_execution_attestation.py",
    "scripts/run_execution_validator.py",
    "scripts/seal_release.py",
    "scripts/abx_acceptance.sh",
    "scripts/run_baseline_seal.py",
    "scripts/run_closure_generalized_attestation.py",
    "scripts/run_promotion_audit.py",
    "scripts/run_promotion_pack.py",
    "scripts/run_receiver_acceptance_audit.py",
    "scripts/run_large_run_promotion_barrier.py",
    "tools/acceptance/run_acceptance_suite.py",
}

CLASSIFIED_CLI_SUBCOMMANDS = {
    "proof-run",
    "promotion-check",
    "promotion-policy",
    "acceptance",
}

CLASSIFIED_MAKE_TARGETS = {
    "proof",
    "proof-run",
    "proof-check",
    "proof-lookup",
    "proof-summary",
    "validate-proof-summary",
    "promotion-check",
    "promotion-policy",
    "attest",
    "seal",
    "governance-lint",
    "governance-summary",
}


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def run_lint() -> dict[str, object]:
    readme = _read("README.md")
    makefile = _read("Makefile")
    runtime_doc = _read("docs/CANONICAL_RUNTIME.md")
    validation_doc = _read("docs/VALIDATION_AND_ATTESTATION.md")
    release_doc = _read("docs/RELEASE_READINESS.md")
    inventory_doc = _read("docs/SUBSYSTEM_INVENTORY.md")
    cli_py = _read("abx/cli.py")
    shared_projection = _read("shared/operatorProjection.ts")
    server_routes = _read("server/routes.ts")

    errors: list[str] = []

    for marker in CANONICAL_COMMAND_MARKERS:
        if (
            marker not in readme
            and marker not in makefile
            and marker not in runtime_doc
            and marker not in release_doc
            and marker not in cli_py
            and marker not in server_routes
        ):
            errors.append(f"missing_canonical_marker:{marker}")

    for marker in REQUIRED_TIER_MARKERS:
        if marker not in readme or marker not in validation_doc:
            errors.append(f"missing_tier_marker:{marker}")

    if "SHADOW_DIAGNOSTIC" not in inventory_doc:
        errors.append("missing_shadow_classification_label")
    if "DEPRECATE_OR_RETIRE" not in inventory_doc:
        errors.append("missing_deprecate_or_retire_label")

    discovered = sorted(
        f"scripts/{p.name}"
        for p in Path("scripts").glob("*")
        if p.is_file() and HEAVY_SCRIPT_PATTERN.search(p.name)
    )
    unclassified = sorted(path for path in discovered if path not in CLASSIFIED_PATHS)
    if unclassified:
        errors.append(f"unclassified_heavy_paths:{','.join(unclassified)}")

    cli_commands = sorted(set(re.findall(r'sub\.add_parser\("([^"]+)"', cli_py)))
    heavy_cli_commands = sorted(
        cmd for cmd in cli_commands if re.search(r"(acceptance|attest|promotion|proof|seal|execution)", cmd)
    )
    unclassified_cli = sorted(cmd for cmd in heavy_cli_commands if cmd not in CLASSIFIED_CLI_SUBCOMMANDS)
    if unclassified_cli:
        errors.append(f"unclassified_cli_commands:{','.join(unclassified_cli)}")

    make_targets = sorted(set(re.findall(r"^([a-zA-Z0-9_-]+):$", makefile, flags=re.MULTILINE)))
    heavy_make_targets = sorted(
        target for target in make_targets if re.search(r"(acceptance|attest|promotion|proof|seal|governance)", target)
    )
    unclassified_make = sorted(target for target in heavy_make_targets if target not in CLASSIFIED_MAKE_TARGETS)
    if unclassified_make:
        errors.append(f"unclassified_make_targets:{','.join(unclassified_make)}")

    for token in [
        "promotion_policy_state",
        "promotion_policy_reason_codes",
        "promotion_policy_requires_federation",
        "promotion_policy_waived",
        "federated_evidence_state_summary",
        "remote_evidence_packet_count",
        "federated_inconsistency_flag",
        "RunSummaryView",
        "RunDiffSummary",
        "EvidenceView",
        "ReleaseReadinessView",
    ]:
        if token not in shared_projection:
            errors.append(f"missing_projection_token_shared:{token}")
        if token not in server_routes:
            errors.append(f"missing_projection_token_server:{token}")

    if "legacy acceptance command" not in runtime_doc:
        errors.append("runtime_doc_missing_legacy_acceptance_boundary")
    if "RemoteEvidenceManifest.v1" not in runtime_doc and "RemoteEvidenceManifest.v1" not in validation_doc and "RemoteEvidenceManifest.v1" not in release_doc:
        errors.append("missing_remote_evidence_manifest_boundary")

    return {
        "ok": not errors,
        "errors": errors,
        "discovered_heavy_paths": discovered,
        "classified_heavy_paths": sorted(CLASSIFIED_PATHS),
        "classified_cli_subcommands": sorted(CLASSIFIED_CLI_SUBCOMMANDS),
        "discovered_heavy_cli_subcommands": heavy_cli_commands,
        "classified_make_targets": sorted(CLASSIFIED_MAKE_TARGETS),
        "discovered_heavy_make_targets": heavy_make_targets,
    }


def main() -> int:
    report = run_lint()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
