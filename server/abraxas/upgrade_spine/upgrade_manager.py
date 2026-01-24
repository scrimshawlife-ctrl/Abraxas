from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jsonschema import ValidationError, validate

from abraxas.core.provenance import hash_bytes, hash_canonical_json
from server.abraxas.upgrade_spine.adapters.drift_adapter import collect_drift_candidates
from server.abraxas.upgrade_spine.adapters.evogate_adapter import collect_evogate_candidates
from server.abraxas.upgrade_spine.adapters.rent_adapter import collect_rent_candidates
from server.abraxas.upgrade_spine.adapters.shadow_adapter import collect_shadow_candidates
from server.abraxas.upgrade_spine.ledger import UpgradeSpineLedger, environment_fingerprint
from server.abraxas.upgrade_spine.types import (
    GateReport,
    UpgradeCandidate,
    UpgradeDecision,
    UpgradeProvenanceBundle,
)
from server.abraxas.upgrade_spine.utils import (
    compute_candidate_id,
    sort_candidates,
    stable_input_hash,
    utc_now_iso,
)


ROOT_PATH = Path(__file__).resolve().parents[3]


@dataclass
class PatchArtifact:
    patch_diff: str
    inputs_manifest: Dict[str, Any]
    replay_commands: List[str]
    sandbox_root: Path
    sandbox_mode: str


class UpgradeSandbox:
    def __init__(self, base_path: Path, candidate_id: str) -> None:
        self.base_path = base_path
        self.candidate_id = candidate_id
        self.sandbox_root = base_path / ".aal" / "sandboxes" / "upgrade_spine" / candidate_id
        self._created = False
        self._use_git = False

    def __enter__(self) -> Path:
        if self.sandbox_root.exists():
            shutil.rmtree(self.sandbox_root)
        self.sandbox_root.parent.mkdir(parents=True, exist_ok=True)
        self._use_git = self._try_git_worktree()
        if not self._use_git:
            self._copy_tree()
        self._created = True
        return self.sandbox_root

    def __exit__(self, exc_type, exc, tb) -> None:
        if not self._created:
            return
        self.cleanup()

    def create(self) -> Path:
        if self.sandbox_root.exists():
            shutil.rmtree(self.sandbox_root)
        self.sandbox_root.parent.mkdir(parents=True, exist_ok=True)
        self._use_git = self._try_git_worktree()
        if not self._use_git:
            self._copy_tree()
        self._created = True
        return self.sandbox_root

    def cleanup(self) -> None:
        if not self._created:
            return
        if self._use_git:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(self.sandbox_root)],
                cwd=self.base_path,
                check=False,
            )
        else:
            shutil.rmtree(self.sandbox_root, ignore_errors=True)

    def _try_git_worktree(self) -> bool:
        if not (self.base_path / ".git").exists():
            return False
        result = subprocess.run(
            ["git", "worktree", "add", "--detach", str(self.sandbox_root)],
            cwd=self.base_path,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def _copy_tree(self) -> None:
        def _ignore(dir_path: str, names: List[str]) -> List[str]:
            ignore = {
                ".git",
                "node_modules",
                "out",
                ".aal",
                "__pycache__",
                ".pytest_cache",
            }
            return [name for name in names if name in ignore]

        shutil.copytree(self.base_path, self.sandbox_root, ignore=_ignore)


def _load_schema(schema_path: Path) -> Dict[str, Any]:
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _validate_schema(payload: Dict[str, Any], schema_path: Path) -> Tuple[bool, Optional[str]]:
    try:
        schema = _load_schema(schema_path)
        validate(instance=payload, schema=schema)
        return True, None
    except ValidationError as exc:
        return False, exc.message


def _hash_file(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    return hash_bytes(path.read_bytes())


def _artifact_hashes(artifact_dir: Path) -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for name in [
        "patch.diff",
        "decision.json",
        "gate_report.json",
        "inputs_manifest.json",
        "replay_instructions.txt",
    ]:
        path = artifact_dir / name
        digest = _hash_file(path)
        if digest:
            hashes[name] = digest
    return hashes


def _load_bundle(artifact_dir: Path) -> UpgradeProvenanceBundle:
    provenance_path = artifact_dir / "provenance.json"
    if not provenance_path.exists():
        raise ValueError(f"Missing provenance bundle: {provenance_path}")
    payload = json.loads(provenance_path.read_text(encoding="utf-8"))
    return UpgradeProvenanceBundle(**payload)


def finalize_artifact_bundle(artifact_dir: Path, bundle_dict: Dict[str, Any]) -> Dict[str, Any]:
    bundle_dict["artifact_hashes"] = _artifact_hashes(artifact_dir)
    provenance_path = artifact_dir / "provenance.json"
    provenance_path.write_text(
        json.dumps(bundle_dict, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return bundle_dict


def _write_patch_file(path: Path, patch_diff: str) -> None:
    path.write_text(patch_diff, encoding="utf-8")


def _default_artifact_dir(base_path: Path, candidate_id: str) -> Path:
    return base_path / ".aal" / "artifacts" / "upgrade_spine" / utc_now_iso()[:10] / candidate_id


def _run_command(cmd: List[str], cwd: Path) -> Tuple[int, str]:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, output


def _apply_patch_plan(candidate: UpgradeCandidate, sandbox_root: Path) -> Dict[str, Any]:
    notes: List[str] = []
    for op in candidate.patch_plan.get("operations", []):
        op_type = op.get("op")
        if op_type == "write_file":
            rel = Path(op["path"])
            dest = sandbox_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(op["content"], encoding="utf-8")
        elif op_type == "apply_patch":
            patch = op.get("patch", "")
            if not patch:
                raise ValueError("apply_patch missing patch content")
            result = subprocess.run(
                ["git", "apply", "-"],
                cwd=sandbox_root,
                input=patch,
                text=True,
                capture_output=True,
            )
            if result.returncode != 0:
                raise ValueError(f"git apply failed: {result.stderr}")
        elif op_type == "copy_file":
            src = sandbox_root / op["src"]
            dest = sandbox_root / op["dest"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        elif op_type == "param_override":
            overrides_file = sandbox_root / "data" / "evolution" / "param_overrides.yaml"
            overrides_file.parent.mkdir(parents=True, exist_ok=True)
            if overrides_file.exists():
                try:
                    overrides = json.loads(overrides_file.read_text())
                except json.JSONDecodeError:
                    overrides = {}
            else:
                overrides = {}
            overrides.setdefault("overrides", [])
            overrides["overrides"].append({
                "param_path": op.get("param_path"),
                "value": op.get("value"),
                "previous_value": op.get("previous_value"),
                "promoted_at": utc_now_iso(),
                "candidate_id": op.get("candidate_id"),
                "rationale": op.get("rationale"),
            })
            overrides_file.write_text(
                json.dumps(overrides, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        elif op_type == "implementation_ticket":
            tickets_dir = sandbox_root / "data" / "evolution" / "implementation_tickets"
            tickets_dir.mkdir(parents=True, exist_ok=True)
            ticket_path = tickets_dir / f"{op['ticket_id']}.json"
            ticket_path.write_text(
                json.dumps(op["payload"], indent=2, sort_keys=True),
                encoding="utf-8",
            )
        else:
            raise ValueError(f"Unsupported patch operation: {op_type}")
    return {"notes": notes}


def _render_inputs_manifest(
    sandbox_root: Path,
    target_paths: List[str],
    evidence_refs: List[str],
) -> Dict[str, Any]:
    manifest: Dict[str, Any] = {"targets": {}, "evidence": {}}
    for rel in sorted(set(target_paths)):
        if not rel:
            continue
        path = sandbox_root / rel
        manifest["targets"][rel] = _hash_file(path)
    for ref in sorted(set(evidence_refs)):
        path = Path(ref)
        if not path.is_absolute():
            path = sandbox_root / ref
        manifest["evidence"][ref] = _hash_file(path)
    return manifest


def collect_candidates(base_path: Optional[Path] = None) -> List[UpgradeCandidate]:
    base_path = base_path or ROOT_PATH
    candidates = []
    candidates.extend(collect_evogate_candidates(base_path))
    candidates.extend(collect_shadow_candidates(base_path))
    candidates.extend(collect_rent_candidates(base_path))
    candidates.extend(collect_drift_candidates(base_path))
    return sort_candidates(candidates)


def evaluate_candidate(candidate: UpgradeCandidate) -> UpgradeDecision:
    input_hash = stable_input_hash(candidate.to_dict())
    reasons: List[str] = []
    status = "ready"
    not_computable = None
    if candidate.not_computable:
        status = "archive"
        reasons.append(candidate.not_computable.get("reason", "not_computable"))
        not_computable = candidate.not_computable
    decision_payload = {
        "candidate_id": candidate.candidate_id,
        "status": status,
        "reasons": reasons,
        "not_computable": not_computable,
    }
    decision_id = compute_candidate_id(decision_payload)
    return UpgradeDecision(
        version="upgrade_decision.v0",
        run_id=candidate.run_id,
        created_at=utc_now_iso(),
        input_hash=input_hash,
        candidate_id=candidate.candidate_id,
        decision_id=decision_id,
        status=status,
        reasons=reasons,
        gate_report=None,
        not_computable=not_computable,
    )


def apply_candidate(
    candidate: UpgradeCandidate,
    base_path: Optional[Path] = None,
) -> Tuple[PatchArtifact, UpgradeProvenanceBundle]:
    base_path = base_path or ROOT_PATH
    sandbox = UpgradeSandbox(base_path, candidate.candidate_id)
    sandbox_root = sandbox.create()
    try:
        _apply_patch_plan(candidate, sandbox_root)
        diff_code, diff_output = _run_command(["git", "diff", "--patch"], sandbox_root)
        patch_diff = diff_output if diff_code == 0 else ""
        inputs_manifest = _render_inputs_manifest(
            sandbox_root,
            candidate.target_paths,
            candidate.evidence_refs,
        )
        replay_commands = [
            f"python tools/run_upgrade_spine.py --apply {candidate.candidate_id}",
        ]
        artifact = PatchArtifact(
            patch_diff=patch_diff,
            inputs_manifest=inputs_manifest,
            replay_commands=replay_commands,
            sandbox_root=sandbox_root,
            sandbox_mode="git_worktree" if sandbox._use_git else "copy",
        )
        artifact_dir = _default_artifact_dir(base_path, candidate.candidate_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        patch_path = artifact_dir / "patch.diff"
        inputs_path = artifact_dir / "inputs_manifest.json"
        replay_path = artifact_dir / "replay_instructions.txt"
        _write_patch_file(patch_path, patch_diff)
        inputs_path.write_text(
            json.dumps(inputs_manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        replay_path.write_text("\n".join(replay_commands) + "\n", encoding="utf-8")
        artifact_paths = {
            "patch.diff": str(patch_path),
            "inputs_manifest.json": str(inputs_path),
            "replay_instructions.txt": str(replay_path),
        }
        artifact_hashes = _artifact_hashes(artifact_dir)
        provenance_payload = {
            "candidate_id": candidate.candidate_id,
            "inputs_manifest": inputs_manifest,
            "artifact_hashes": artifact_hashes,
        }
        bundle = UpgradeProvenanceBundle(
            version="upgrade_provenance_bundle.v0",
            run_id=candidate.run_id,
            created_at=utc_now_iso(),
            input_hash=hash_canonical_json(provenance_payload),
            candidate_id=candidate.candidate_id,
            decision_id="pending",
            environment=environment_fingerprint(base_path),
            artifact_paths=artifact_paths,
            artifact_dir=str(artifact_dir),
            artifact_hashes=artifact_hashes,
            inputs_manifest=inputs_manifest,
            gate_report=None,
        )
        return artifact, bundle
    except Exception:
        sandbox.cleanup()
        raise


def run_gates(
    bundle: UpgradeProvenanceBundle,
    candidate: UpgradeCandidate,
    sandbox_root: Path,
    base_path: Optional[Path] = None,
    gate_overrides: Optional[Dict[str, Any]] = None,
) -> GateReport:
    base_path = base_path or ROOT_PATH
    gate_overrides = gate_overrides or {}
    order = [
        "schema_validation",
        "dozen_run_invariance",
        "rent_enforcement",
        "missing_input",
    ]

    if "schema_validation" in gate_overrides:
        schema_report = gate_overrides["schema_validation"]
    else:
        schema_ok, schema_msg = _validate_schema(
            candidate.to_dict(),
            base_path / "server" / "abraxas" / "schemas" / "UpgradeCandidate.v0.json",
        )
        schema_report = {"ok": schema_ok, "message": schema_msg}

    acceptance_report = gate_overrides.get("dozen_run_invariance")
    if acceptance_report is None:
        input_path = sandbox_root / "tests" / "fixtures" / "acceptance" / "baseline_input.json"
        output_dir = sandbox_root / "out" / "acceptance"
        cmd = [
            "python",
            "tools/acceptance/run_acceptance_suite.py",
            "--input",
            str(input_path),
            "--output",
            str(output_dir),
        ]
        code, output = _run_command(cmd, sandbox_root)
        result_path = output_dir / "acceptance_result.json"
        verdict = "FAIL"
        details: Dict[str, Any] = {"output": output.strip()}
        if code == 0 and result_path.exists():
            result = json.loads(result_path.read_text())
            verdict = result.get("overall_verdict", "FAIL")
            details["result_path"] = str(result_path)
        acceptance_report = {
            "ok": verdict == "PASS",
            "verdict": verdict,
            "details": details,
        }

    rent_report = gate_overrides.get("rent_enforcement")
    if rent_report is None:
        cmd = [
            "python",
            "-m",
            "abraxas.cli.rent_check",
            "--strict",
            "true",
            "--output",
            "out/reports",
        ]
        code, output = _run_command(cmd, sandbox_root)
        report_paths = sorted((sandbox_root / "out" / "reports").glob("rent_check_*.json"))
        passed = False
        details: Dict[str, Any] = {"output": output.strip()}
        if code == 0 and report_paths:
            report = json.loads(report_paths[-1].read_text())
            passed = bool(report.get("passed"))
            details["report_path"] = str(report_paths[-1])
        rent_report = {
            "ok": passed,
            "details": details,
        }

    missing_report = gate_overrides.get("missing_input")
    if missing_report is None:
        missing_ok = candidate.not_computable is None
        missing_report = {
            "ok": missing_ok,
            "details": candidate.not_computable or {},
        }

    overall_ok = all(
        report.get("ok")
        for report in [schema_report, acceptance_report, rent_report, missing_report]
    )

    return GateReport(
        order=order,
        schema_validation=schema_report,
        dozen_run_invariance=acceptance_report,
        rent_enforcement=rent_report,
        missing_input=missing_report,
        overall_ok=overall_ok,
    )


def cleanup_sandbox(artifact: PatchArtifact, base_path: Optional[Path] = None) -> None:
    base_path = base_path or ROOT_PATH
    if artifact.sandbox_mode == "git_worktree":
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(artifact.sandbox_root)],
            cwd=base_path,
            check=False,
        )
    else:
        shutil.rmtree(artifact.sandbox_root, ignore_errors=True)


def promote_or_archive(
    decision: UpgradeDecision,
    bundle: UpgradeProvenanceBundle,
    artifact: PatchArtifact,
    base_path: Optional[Path] = None,
) -> str:
    base_path = base_path or ROOT_PATH
    ledger = UpgradeSpineLedger(base_path)
    if decision.status == "promote" and bundle.gate_report:
        bundle_root = Path(bundle.artifact_dir or _default_artifact_dir(base_path, decision.candidate_id))
        bundle_root.mkdir(parents=True, exist_ok=True)
        patch_path = bundle_root / "patch.diff"
        decision_path = bundle_root / "decision.json"
        provenance_path = bundle_root / "provenance.json"
        gate_path = bundle_root / "gate_report.json"
        inputs_path = bundle_root / "inputs_manifest.json"
        replay_path = bundle_root / "replay_instructions.txt"
        if not patch_path.exists():
            _write_patch_file(patch_path, artifact.patch_diff)
        if not inputs_path.exists():
            inputs_path.write_text(
                json.dumps(artifact.inputs_manifest, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        if not replay_path.exists():
            replay_path.write_text(
                "\n".join(artifact.replay_commands) + "\n",
                encoding="utf-8",
            )
        decision_path.write_text(
            json.dumps(decision.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        gate_path.write_text(
            json.dumps(bundle.gate_report, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        provenance_bundle = bundle.to_dict()
        provenance_bundle["artifact_paths"] = {
            "patch.diff": str(patch_path),
            "decision.json": str(decision_path),
            "provenance.json": str(provenance_path),
            "gate_report.json": str(gate_path),
            "inputs_manifest.json": str(inputs_path),
            "replay_instructions.txt": str(replay_path),
        }
        provenance_bundle["artifact_dir"] = str(bundle_root)
        provenance_bundle["artifact_hashes"] = _artifact_hashes(bundle_root)
        provenance_path.write_text(
            json.dumps(provenance_bundle, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        if patch_path.exists():
            subprocess.run(
                ["git", "apply", str(patch_path)],
                cwd=base_path,
                check=False,
            )
        ledger.append("provenance_bundle", provenance_bundle)
        return ledger.append("promotion", decision.to_dict())

    archive_payload = decision.to_dict()
    archive_payload["archived_at"] = utc_now_iso()
    return ledger.append("archive", archive_payload)


def promote_from_bundle(
    decision: UpgradeDecision,
    artifact_dir: Path,
    base_path: Optional[Path] = None,
) -> str:
    base_path = base_path or ROOT_PATH
    ledger = UpgradeSpineLedger(base_path)
    bundle = _load_bundle(artifact_dir)
    if decision.status != "promote":
        raise ValueError("Decision status not promotable")
    if not decision.gate_report or not decision.gate_report.get("overall_ok"):
        raise ValueError("Gate report not promotable")
    if decision.candidate_id != bundle.candidate_id:
        raise ValueError("Decision candidate_id mismatch")
    if decision.decision_id != bundle.decision_id:
        raise ValueError("Decision decision_id mismatch")
    artifact_hashes = bundle.artifact_hashes or {}
    current_hashes = _artifact_hashes(artifact_dir)
    if not artifact_hashes:
        raise ValueError("Missing artifact hashes in provenance bundle")
    for name, digest in artifact_hashes.items():
        if current_hashes.get(name) != digest:
            raise ValueError(f"Artifact hash mismatch for {name}")
    patch_path = artifact_dir / "patch.diff"
    if not patch_path.exists():
        raise ValueError("Missing patch.diff in artifact bundle")
    result = subprocess.run(
        ["git", "apply", str(patch_path)],
        cwd=base_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or "git apply failed")
    ledger.append("provenance_bundle", bundle.to_dict())
    return ledger.append("promotion", decision.to_dict())
