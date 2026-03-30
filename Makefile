# Abraxas Makefile
# Provides targets for common development and release tasks

.PHONY: help test seal validate clean lint attest proof promotion-check promotion-policy governance-lint release-readiness ts-canonical-check large-chunk large-run-convergence todo-scan

# Default target
help:
	@echo "Abraxas Development Targets"
	@echo "============================"
	@echo ""
	@echo "  make test      - Run pytest test suite"
	@echo "  make seal      - Run seal release diagnostics (shadow; archive-candidate for promotion workflows)"
	@echo "  make validate  - Validate artifacts in ./artifacts_seal"
	@echo "  make attest RUN_ID=<id> - Run unified execution attestation (policy-gated)"
	@echo "  make proof RUN_ID=<id> - Run canonical proof-bearing closure path"
	@echo "  make promotion-check RUN_ID=<id> - Classify local vs promotion readiness"
	@echo "  make promotion-policy RUN_ID=<id> - Enforce promotion permission policy gate"
	@echo "  make governance-lint - Run consolidated canonical/shadow drift guardrails"
	@echo "  make large-run-convergence BATCH_ID=<id> [MIN_POINTERS=1] - Run deterministic large-run convergence bundle"
	@echo "  make large-chunk - Execute Wave 6 chunk plan + evidence report"
	@echo "  make todo-scan - Emit deterministic TODO/FIXME marker artifact"
	@echo "  make clean     - Remove seal/gate artifacts"
	@echo "  make lint      - Run linting (if configured)"
	@echo "  make lexicon-check - Verify ASE lexicon artifacts are up to date"
	@echo "  make lexicon-update - Regenerate ASE lexicon artifacts"
	@echo ""

# Run pytest test suite
test:
	python3 -m pytest tests/ -v

# Run seal release script
# Creates ./artifacts_seal with validated artifacts and SealReport.v0
seal:
	python3 -m scripts.seal_release --run_id seal

# Validate existing artifacts
validate:
	python3 -m scripts.validate_artifacts --artifacts_dir ./artifacts_seal --run_id seal --tick 0

# Run unified execution attestation (validator + acceptance; optional seal via WITH_SEAL=1)
attest:
	python3 scripts/run_execution_attestation.py $(RUN_ID) $(if $(WITH_SEAL),--with-seal,)

# Run canonical proof-bearing closure spine
proof:
	python3 -m abx.cli proof-run --run-id $(RUN_ID)

# Check local closure vs promotion readiness
promotion-check:
	python3 -m abx.cli promotion-check --run-id $(RUN_ID)

# Evaluate promotion policy gate
promotion-policy:
	python3 -m abx.cli promotion-policy --run-id $(RUN_ID)

# Run consolidated governance lint + anti-regrowth checks
governance-lint:
	python3 scripts/run_governance_lint.py

# Narrow TS check for canonical semantic surfaces
ts-canonical-check:
	npx tsc -p tsconfig.canonical.json --pretty false

# Run pre-feature release-readiness checklist
release-readiness:
	python3 scripts/run_release_readiness.py $(if $(RUN_ID),--run-id $(RUN_ID),) --base-dir .

# Run deterministic large-run convergence bundle (coverage + pointer + rune index + barrier)
large-run-convergence:
	python3 scripts/run_large_run_convergence.py --base-dir . --batch-id $(BATCH_ID) --min-pointers $(if $(MIN_POINTERS),$(MIN_POINTERS),1)

# Clean up seal/gate artifacts
clean:
	rm -rf ./artifacts_seal ./artifacts_gate

# Run linting (placeholder - configure as needed)
lint:
	@echo "Linting not configured. Add your linter commands here."

# Run dozen-run gate standalone
gate:
	python3 -m scripts.dozen_run_gate_runtime --artifacts_dir ./artifacts_gate --run_id gate_test --runs 12

# ASE lexicon automation
lexicon-check:
	python3 -m abraxas_ase.tools.lexicon_update --check --in lexicon_sources --out abraxas_ase

lexicon-update:
	python3 -m abraxas_ase.tools.lexicon_update --in lexicon_sources --out abraxas_ase

# Execute Wave 6 large-chunk plan and emit report
large-chunk:
	python3 scripts/run_large_chunk_plan.py

# Emit deterministic TODO/FIXME marker scan artifact
todo-scan:
	python3 scripts/scan_todo_markers.py
