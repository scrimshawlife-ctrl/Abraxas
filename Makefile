# Abraxas Makefile
# Provides targets for common development and release tasks

.PHONY: help test seal validate clean lint attest large-chunk todo-scan

# Default target
help:
	@echo "Abraxas Development Targets"
	@echo "============================"
	@echo ""
	@echo "  make test      - Run pytest test suite"
	@echo "  make seal      - Run seal release validation"
	@echo "  make validate  - Validate artifacts in ./artifacts_seal"
	@echo "  make attest RUN_ID=<id> - Run unified execution attestation"
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
