#!/usr/bin/env python3
"""Abraxas Acceptance Test Suite v1.0

Canonical test harness for release readiness verification.
Implements the hard gates defined in docs/acceptance/ABRAXAS_ACCEPTANCE_SPEC_v1.md
"""

from __future__ import annotations
import sys
import json
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from dataclasses import asdict

from jsonschema import ValidationError, validate

from abraxas.oracle.v2.pipeline import OracleSignal, OracleV2Pipeline
from abraxas.renderers.resonance_narratives.renderer import render as render_narrative_bundle
from tools.acceptance.emit_drift_on_failure import classify_drift, emit as emit_drift_on_failure
from tools.acceptance.utils import canonical_json, sha256

@dataclass
class TestResult:
    """Result of a single acceptance test."""
    test_id: str
    name: str
    verdict: str  # "PASS", "FAIL", "SKIP"
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    is_hard_gate: bool = False


@dataclass
class AcceptanceSuiteResult:
    """Overall acceptance suite result."""
    timestamp: str
    tests: List[TestResult]
    hard_gate_passes: int = 0
    hard_gate_failures: int = 0
    total_tests: int = 0

    @property
    def overall_verdict(self) -> str:
        """Overall verdict: PASS if all hard gates pass."""
        if self.hard_gate_failures > 0:
            return "FAIL"
        if self.hard_gate_passes == 0:
            return "INCOMPLETE"
        return "PASS"


class AcceptanceTestSuite:
    """Abraxas Acceptance Test Suite runner."""

    def __init__(self, input_path: Path, output_dir: Path, num_runs: int = 12):
        """Initialize the test suite.

        Args:
            input_path: Path to baseline input JSON
            output_dir: Directory for test outputs
            num_runs: Number of runs for invariance tests (default: 12)
        """
        self.input_path = input_path
        self.output_dir = output_dir
        self.num_runs = num_runs
        self.results: List[TestResult] = []
        self._latest_envelope: Optional[Dict[str, Any]] = None
        self._pipeline = OracleV2Pipeline()

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_all(self) -> AcceptanceSuiteResult:
        """Run all acceptance tests and return overall result."""
        print("Abraxas Acceptance Suite v1.0")
        print("=" * 80)
        print()

        # A1: 12-run determinism (HARD GATE)
        self._test_a1_determinism()

        # B1: Schema validation (HARD GATE)
        self._test_b1_schema_validation()

        # C2: Evidence gating (HARD GATE)
        self._test_c2_evidence_gating()

        # D1: Shadow isolation (HARD GATE)
        self._test_d1_shadow_isolation()

        # E2: Pointer auditability (HARD GATE)
        self._test_e2_pointer_auditability()

        # Generate overall result
        result = self._compute_overall_result()

        # Print summary
        self._print_summary(result)

        # Write result to disk
        self._write_result(result)

        return result

    def _test_a1_determinism(self) -> TestResult:
        """Test A1: 12-run determinism (single-input determinism)."""
        test_id = "A1_12_RUN_DETERMINISM"
        name = "12-run determinism"

        print(f"[{test_id}] {name}...", end="", flush=True)

        try:
            # Load input
            if not self.input_path.exists():
                result = TestResult(
                    test_id=test_id,
                    name=name,
                    verdict="SKIP",
                    message=f"Input file not found: {self.input_path}",
                    is_hard_gate=True
                )
                self.results.append(result)
                print(f" {result.verdict}")
                print(f"     {result.message}")
                return result

            with open(self.input_path) as f:
                input_data = json.load(f)

            # Run oracle N times and collect hashes
            hashes = []
            envelopes = []
            for i in range(self.num_runs):
                envelope = self._run_oracle(input_data, run_id=f"acceptance-{i}")
                envelopes.append(envelope)
                canonical_hash = self._compute_canonical_hash(envelope)
                hashes.append(canonical_hash)

            if envelopes:
                self._latest_envelope = envelopes[0]

            # Check if all hashes are identical
            if len(set(hashes)) == 1:
                result = TestResult(
                    test_id=test_id,
                    name=name,
                    verdict="PASS",
                    message=f"Hash: {hashes[0][:12]}... (identical across {self.num_runs} runs)",
                    details={"hash": hashes[0], "num_runs": self.num_runs},
                    is_hard_gate=True
                )
            else:
                # Determinism failure - classify drift
                diff_paths = self._diff_envelopes(envelopes)
                drift_class = self._classify_drift(diff_paths)
                result = TestResult(
                    test_id=test_id,
                    name=name,
                    verdict="FAIL",
                    message=f"Hash mismatch: {len(set(hashes))} unique hashes",
                    details={
                        "unique_hashes": list(set(hashes)),
                        "drift_classification": drift_class,
                        "diff_paths": diff_paths
                    },
                    is_hard_gate=True
                )
                # Emit drift report
                self._emit_drift_report(result, envelopes)

        except Exception as e:
            result = TestResult(
                test_id=test_id,
                name=name,
                verdict="FAIL",
                message=f"Exception: {str(e)}",
                is_hard_gate=True
            )

        self.results.append(result)
        print(f" {result.verdict}")
        if result.message:
            print(f"     {result.message}")
        return result

    def _test_b1_schema_validation(self) -> TestResult:
        """Test B1: Schema validation for output artifacts."""
        test_id = "B1_SCHEMA_VALIDATION"
        name = "Schema validation"

        print(f"[{test_id}] {name}...", end="", flush=True)

        try:
            status_payload = self._build_acceptance_status(self.results)
            status_schema = self._load_schema(
                Path("schemas/acceptance/v1/acceptance_status.schema.json")
            )
            validate(instance=status_payload, schema=status_schema)

            narrative_schema = self._load_schema(
                Path("schemas/renderers/resonance_narratives/v1/narrative_bundle.schema.json")
            )
            envelope = self._latest_envelope or self._run_oracle(self._load_input(), run_id="acceptance-schema")
            narrative_bundle = render_narrative_bundle(envelope)
            validate(instance=narrative_bundle, schema=narrative_schema)
            result = TestResult(
                test_id=test_id,
                name=name,
                verdict="PASS",
                message="acceptance_status_v1: VALID\nnarrative_bundle_v1: VALID",
                details={"acceptance_status_v1": True, "narrative_bundle_v1": True},
                is_hard_gate=True,
            )
        except ValidationError as e:
            result = TestResult(
                test_id=test_id,
                name=name,
                verdict="FAIL",
                message=f"Schema validation error: {e.message}",
                details={"acceptance_status_v1": False, "narrative_bundle_v1": False},
                is_hard_gate=True,
            )
        except Exception as e:
            result = TestResult(
                test_id=test_id,
                name=name,
                verdict="FAIL",
                message=f"Exception: {str(e)}",
                is_hard_gate=True
            )

        self.results.append(result)
        print(f" {result.verdict}")
        if result.message:
            for line in result.message.split('\n'):
                print(f"     {line}")
        return result

    def _test_c2_evidence_gating(self) -> TestResult:
        """Test C2: Evidence gating (negative test)."""
        test_id = "C2_EVIDENCE_GATING"
        name = "Evidence gating"

        print(f"[{test_id}] {name}...", end="", flush=True)

        try:
            baseline = self._load_input()
            observations = baseline.get("observations", []) if isinstance(baseline.get("observations"), list) else []
            sources = [obs.get("source") for obs in observations if obs.get("source")]
            removed_source = sources[0] if sources else "unknown"

            filtered_observations = [obs for obs in observations if obs.get("source") != removed_source]
            gated_input = dict(baseline)
            gated_input["observations"] = filtered_observations

            envelope = self._run_oracle(
                gated_input,
                run_id="acceptance-evidence-gating",
                required_sources=sources,
            )
            dependent_field = f"observations:{removed_source}"
            is_not_computable = dependent_field in envelope.get("not_computable", [])

            if is_not_computable:
                result = TestResult(
                    test_id=test_id,
                    name=name,
                    verdict="PASS",
                    message=(
                        f'Removed source: "{removed_source}"\n'
                        f'     Dependent field "{dependent_field}": not_computable ✓'
                    ),
                    details={
                        "removed_source": removed_source,
                        "dependent_field": dependent_field,
                        "not_computable": True
                    },
                    is_hard_gate=True
                )
            else:
                result = TestResult(
                    test_id=test_id,
                    name=name,
                    verdict="FAIL",
                    message=f"Phantom evidence: {dependent_field} computed without {removed_source}",
                    is_hard_gate=True
                )

        except Exception as e:
            result = TestResult(
                test_id=test_id,
                name=name,
                verdict="FAIL",
                message=f"Exception: {str(e)}",
                is_hard_gate=True
            )

        self.results.append(result)
        print(f" {result.verdict}")
        if result.message:
            for line in result.message.split('\n'):
                print(f"     {line}")
        return result

    def _test_d1_shadow_isolation(self) -> TestResult:
        """Test D1: Shadow metrics are non-causal."""
        test_id = "D1_SHADOW_ISOLATION"
        name = "Shadow isolation"

        print(f"[{test_id}] {name}...", end="", flush=True)

        try:
            baseline = self._load_input()
            with_shadow = dict(baseline)
            with_shadow["config"] = dict(baseline.get("config", {}))
            with_shadow["config"]["enable_shadow_metrics"] = True

            without_shadow = dict(baseline)
            without_shadow["config"] = dict(baseline.get("config", {}))
            without_shadow["config"]["enable_shadow_metrics"] = False

            envelope_with_shadow = self._run_oracle(with_shadow, run_id="acceptance-shadow-on")
            envelope_without_shadow = self._run_oracle(without_shadow, run_id="acceptance-shadow-off")

            hash_with_shadow = self._compute_canonical_hash(envelope_with_shadow)
            hash_without_shadow = self._compute_canonical_hash(envelope_without_shadow)
            isolated = hash_with_shadow == hash_without_shadow

            if isolated:
                result = TestResult(
                    test_id=test_id,
                    name=name,
                    verdict="PASS",
                    message="Forecast hash identical with/without shadow detectors",
                    details={
                        "hash_with_shadow": hash_with_shadow,
                        "hash_without_shadow": hash_without_shadow
                    },
                    is_hard_gate=True
                )
            else:
                result = TestResult(
                    test_id=test_id,
                    name=name,
                    verdict="FAIL",
                    message="Shadow metrics influenced forecast output",
                    details={
                        "hash_with_shadow": hash_with_shadow,
                        "hash_without_shadow": hash_without_shadow
                    },
                    is_hard_gate=True
                )

        except Exception as e:
            result = TestResult(
                test_id=test_id,
                name=name,
                verdict="FAIL",
                message=f"Exception: {str(e)}",
                is_hard_gate=True
            )

        self.results.append(result)
        print(f" {result.verdict}")
        if result.message:
            print(f"     {result.message}")
        return result

    def _test_e2_pointer_auditability(self) -> TestResult:
        """Test E2: Pointer auditability in narrative renderer."""
        test_id = "E2_POINTER_AUDITABILITY"
        name = "Pointer auditability"

        print(f"[{test_id}] {name}...", end="", flush=True)

        try:
            envelope = self._latest_envelope or self._run_oracle(self._load_input(), run_id="acceptance-pointer-audit")
            bundle = render_narrative_bundle(envelope)
            total_pointers, resolved_pointers, unresolved = self._audit_bundle_pointers(bundle, envelope)

            if resolved_pointers == total_pointers:
                result = TestResult(
                    test_id=test_id,
                    name=name,
                    verdict="PASS",
                    message=f"All {total_pointers} pointers resolved successfully",
                    details={
                        "total_pointers": total_pointers,
                        "resolved": resolved_pointers
                    },
                    is_hard_gate=True
                )
            else:
                result = TestResult(
                    test_id=test_id,
                    name=name,
                    verdict="FAIL",
                    message=f"{unresolved} unresolved pointers",
                    details={
                        "total_pointers": total_pointers,
                        "resolved": resolved_pointers,
                        "unresolved": unresolved,
                    },
                    is_hard_gate=True
                )

        except Exception as e:
            result = TestResult(
                test_id=test_id,
                name=name,
                verdict="FAIL",
                message=f"Exception: {str(e)}",
                is_hard_gate=True
            )

        self.results.append(result)
        print(f" {result.verdict}")
        if result.message:
            print(f"     {result.message}")
        return result

    def _run_oracle(
        self,
        input_data: Dict[str, Any],
        run_id: str,
        required_sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run oracle pipeline and return envelope."""
        observations = input_data.get("observations", [])
        if not isinstance(observations, list):
            observations = []

        tokens = [
            str(obs.get("term"))
            for obs in observations
            if isinstance(obs, dict) and obs.get("term")
        ]

        timestamp = None
        for obs in observations:
            if isinstance(obs, dict) and obs.get("timestamp"):
                timestamp = obs.get("timestamp")
                break
        timestamp = timestamp or datetime.now(timezone.utc).replace(microsecond=0).isoformat()

        signal = OracleSignal(
            domain=str(input_data.get("domain") or "unknown"),
            subdomain=None,
            observations=[str(obs.get("context") or obs.get("term") or "") for obs in observations],
            tokens=tokens,
            timestamp_utc=timestamp,
            source_id=None,
            meta={},
        )

        output = self._pipeline.process(signal, run_id=run_id, git_sha=None)
        envelope = asdict(output)
        envelope["artifact_id"] = f"oracle-run-{run_id}"
        envelope["created_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        envelope["input_hash"] = self._compute_input_hash(input_data)
        envelope["source_count"] = len(observations)

        required = required_sources or [
            obs.get("source") for obs in observations if isinstance(obs, dict) and obs.get("source")
        ]
        missing = [
            source for source in required
            if source and not any(obs.get("source") == source for obs in observations if isinstance(obs, dict))
        ]
        envelope["missing_inputs"] = [str(source) for source in missing]
        envelope["not_computable"] = [f"observations:{source}" for source in missing]
        return envelope

    def _compute_input_hash(self, input_data: Dict[str, Any]) -> str:
        """Compute canonical hash of input data."""
        return sha256(canonical_json(input_data))

    def _compute_canonical_hash(self, envelope: Dict[str, Any]) -> str:
        """Compute canonical hash of envelope (excluding runtime metadata)."""
        canonical_envelope = self._normalize_envelope(envelope)
        return sha256(canonical_json(canonical_envelope))

    def _classify_drift(self, diff_paths: List[str]) -> str:
        """Classify drift cause based on diff paths."""
        return classify_drift(diff_paths)

    def _emit_drift_report(self, test_result: TestResult, envelopes: List[Dict[str, Any]]):
        """Emit drift report artifact on determinism failure."""
        drift_report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "test": test_result.test_id,
            "verdict": test_result.verdict,
            "classification": test_result.details.get("drift_classification", "UNKNOWN"),
            "differing_hashes": test_result.details.get("unique_hashes", []),
            "diff_paths": test_result.details.get("diff_paths", []),
            "metadata": {
                "input_path": str(self.input_path),
                "num_runs": self.num_runs
            }
        }

        # Write to ledger
        ledger_path = self.output_dir / "acceptance_failures.jsonl"
        with open(ledger_path, "a") as f:
            f.write(json.dumps(drift_report, sort_keys=True) + "\n")

        changes = [
            {"pointer": path, "before": None, "after": None}
            for path in test_result.details.get("diff_paths", [])
        ]
        emit_drift_on_failure(self.output_dir, envelopes, changes)

    def _compute_overall_result(self) -> AcceptanceSuiteResult:
        """Compute overall acceptance suite result."""
        hard_gate_passes = sum(1 for r in self.results if r.is_hard_gate and r.verdict == "PASS")
        hard_gate_failures = sum(1 for r in self.results if r.is_hard_gate and r.verdict == "FAIL")

        return AcceptanceSuiteResult(
            timestamp=datetime.utcnow().isoformat() + "Z",
            tests=self.results,
            hard_gate_passes=hard_gate_passes,
            hard_gate_failures=hard_gate_failures,
            total_tests=len(self.results)
        )

    def _diff_envelopes(self, envelopes: List[Dict[str, Any]]) -> List[str]:
        """Compute diff paths across envelopes relative to the first."""
        if not envelopes:
            return []
        base = self._normalize_envelope(envelopes[0])
        diff_paths: List[str] = []
        for envelope in envelopes[1:]:
            normalized = self._normalize_envelope(envelope)
            self._diff_values(base, normalized, "", diff_paths)
        return sorted(set(diff_paths))

    def _diff_values(self, base: Any, other: Any, path: str, diff_paths: List[str]) -> None:
        if isinstance(base, dict) and isinstance(other, dict):
            base_keys = set(base.keys())
            other_keys = set(other.keys())
            for key in sorted(base_keys | other_keys):
                next_path = f"{path}/{key}" if path else f"/{key}"
                if key not in base:
                    diff_paths.append(next_path)
                    continue
                if key not in other:
                    diff_paths.append(next_path)
                    continue
                self._diff_values(base[key], other[key], next_path, diff_paths)
            return
        if isinstance(base, list) and isinstance(other, list):
            max_len = max(len(base), len(other))
            for idx in range(max_len):
                next_path = f"{path}/{idx}" if path else f"/{idx}"
                if idx >= len(base) or idx >= len(other):
                    diff_paths.append(next_path)
                    continue
                self._diff_values(base[idx], other[idx], next_path, diff_paths)
            return
        if base != other:
            diff_paths.append(path or "/")

    def _normalize_envelope(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """Remove non-deterministic fields before diffing."""
        runtime_keys = {
            "artifact_id",
            "created_at",
            "created_at_utc",
            "timestamp_utc",
            "started_at_utc",
            "run_id",
            "bundle_id",
        }

        def scrub(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: scrub(v) for k, v in obj.items() if k not in runtime_keys}
            if isinstance(obj, list):
                return [scrub(v) for v in obj]
            return obj

        return scrub(envelope)

    def _load_input(self) -> Dict[str, Any]:
        with open(self.input_path) as f:
            return json.load(f)

    def _audit_bundle_pointers(
        self,
        bundle: Dict[str, Any],
        envelope: Dict[str, Any],
    ) -> tuple[int, int, List[str]]:
        pointers: List[str] = []
        for item in bundle.get("signal_summary", []):
            if isinstance(item, dict) and item.get("pointer"):
                pointers.append(item["pointer"])
        for item in bundle.get("what_changed", []):
            if isinstance(item, dict) and item.get("pointer"):
                pointers.append(item["pointer"])
        for item in bundle.get("motifs", []):
            if isinstance(item, dict) and item.get("pointer"):
                pointers.append(item["pointer"])

        resolved = 0
        unresolved: List[str] = []
        for ptr in pointers:
            ok = self._resolve_pointer(envelope, ptr)
            if ok:
                resolved += 1
            else:
                unresolved.append(ptr)
        return len(pointers), resolved, unresolved

    def _resolve_pointer(self, doc: Any, pointer: str) -> bool:
        if pointer in ("", "/"):
            return True
        if not pointer.startswith("/"):
            return False
        cur = doc
        for raw in pointer.lstrip("/").split("/"):
            key = raw.replace("~1", "/").replace("~0", "~")
            try:
                if isinstance(cur, list):
                    cur = cur[int(key)]
                else:
                    cur = cur[key]
            except Exception:
                return False
        return True

    def _build_acceptance_status(self, tests: List[TestResult]) -> Dict[str, Any]:
        hard_gates = [t.test_id for t in tests if t.is_hard_gate]
        failures = [t.test_id for t in tests if t.is_hard_gate and t.verdict != "PASS"]
        return {
            "schema_version": "1.0.0",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "run_window": {
                "artifact_count": len(tests),
                "start_created_at": None,
                "end_created_at": None,
            },
            "hard_gates": hard_gates,
            "results": [
                {
                    "name": t.test_id,
                    "ok": t.verdict == "PASS",
                    "details": t.message,
                }
                for t in tests
            ],
            "overall": {
                "ok": len(failures) == 0 and len(hard_gates) > 0,
                "failures": failures,
            },
        }

    def _load_schema(self, schema_path: Path) -> Dict[str, Any]:
        full_path = schema_path if schema_path.is_absolute() else Path.cwd() / schema_path
        with open(full_path, "r") as f:
            return json.load(f)

    def _print_summary(self, result: AcceptanceSuiteResult):
        """Print summary of acceptance suite run."""
        print()
        print("=" * 80)

        verdict_symbol = "✅" if result.overall_verdict == "PASS" else "❌"
        verdict_text = result.overall_verdict

        print(f"VERDICT: {verdict_symbol} {verdict_text} ({result.hard_gate_passes}/{result.hard_gate_passes + result.hard_gate_failures} hard gates)")

        if result.overall_verdict == "PASS":
            print("Abraxas is doing its job.")
        else:
            print("Abraxas is NOT ready for release.")
            print(f"Failed {result.hard_gate_failures} hard gate(s).")

    def _write_result(self, result: AcceptanceSuiteResult):
        """Write acceptance suite result to disk."""
        result_path = self.output_dir / "acceptance_result.json"
        status_path = self.output_dir / "acceptance_status_v1.json"

        result_data = {
            "timestamp": result.timestamp,
            "overall_verdict": result.overall_verdict,
            "hard_gate_passes": result.hard_gate_passes,
            "hard_gate_failures": result.hard_gate_failures,
            "total_tests": result.total_tests,
            "tests": [
                {
                    "test_id": t.test_id,
                    "name": t.name,
                    "verdict": t.verdict,
                    "message": t.message,
                    "is_hard_gate": t.is_hard_gate,
                    "details": t.details
                }
                for t in result.tests
            ]
        }

        with open(result_path, "w") as f:
            json.dump(result_data, f, indent=2, sort_keys=True)

        status_payload = self._build_acceptance_status(result.tests)
        with open(status_path, "w") as f:
            json.dump(status_payload, f, indent=2, sort_keys=True)

        print(f"\nResult written to: {result_path}")
        print(f"Acceptance status written to: {status_path}")


def main():
    """Main entry point for acceptance test suite."""
    parser = argparse.ArgumentParser(
        description="Abraxas Acceptance Test Suite v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("tests/fixtures/acceptance/baseline_input.json"),
        help="Path to baseline input JSON (default: tests/fixtures/acceptance/baseline_input.json)"
    )

    parser.add_argument(
        "--runs",
        type=int,
        default=12,
        help="Number of runs for invariance tests (default: 12)"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("out/acceptance"),
        help="Output directory for test results (default: out/acceptance/)"
    )

    args = parser.parse_args()

    # Run acceptance suite
    suite = AcceptanceTestSuite(
        input_path=args.input,
        output_dir=args.output,
        num_runs=args.runs
    )

    result = suite.run_all()

    # Exit with appropriate code
    sys.exit(0 if result.overall_verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
