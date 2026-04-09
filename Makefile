PYTHON ?= python

preflight:
	$(PYTHON) .abraxas/scripts/preflight.py --subsystem $(or $(SUBSYSTEM),oracle_signal_layer_v2) $(if $(CHANGE_CLASS),--change-class $(CHANGE_CLASS),)

preflight-oracle_signal_layer_v2:
	$(PYTHON) .abraxas/scripts/preflight.py --subsystem oracle_signal_layer_v2
preflight-mbom_v1:
	$(PYTHON) .abraxas/scripts/preflight.py --subsystem mbom_v1
preflight-mircl_v1:
	$(PYTHON) .abraxas/scripts/preflight.py --subsystem mircl_v1
preflight-forecast_portfolio_simulation_v0_1:
	$(PYTHON) .abraxas/scripts/preflight.py --subsystem forecast_portfolio_simulation_v0_1

scaffold:
	$(PYTHON) .abraxas/scripts/scaffold_drop.py --out /tmp/code_drop_envelope.md
proof-check:
	$(PYTHON) .abraxas/scripts/check_proof_claims.py --path .abraxas/templates
registry-check:
	$(PYTHON) .abraxas/scripts/registry_consistency.py
proof-lookup:
	$(PYTHON) .abraxas/scripts/proof_requirement_lookup.py --subsystem oracle_signal_layer_v2 --change-class forecast_active_change
governance-lint:
	$(PYTHON) .abraxas/scripts/governance_lint.py
release-readiness:
	$(PYTHON) .abraxas/scripts/release_readiness.py --subsystem oracle_signal_layer_v2 --receipts runtime_artifact validator_artifact
append-record:
	$(PYTHON) .abraxas/scripts/append_governance_record.py --record .abraxas/templates/promotion_decision_record.json --ledger .abraxas/ledger/promotion_decisions.jsonl
proof-run:
	@if [ -z "$(SUBSYSTEM)" ]; then \
		echo "Usage: make proof-run SUBSYSTEM=<name>"; \
		exit 2; \
	fi
	$(PYTHON) scripts/run_proof.py --subsystem $(SUBSYSTEM)
capture-receipts:
	@if [ -z "$(SUBSYSTEM)" ] || [ -z "$(OUT)" ]; then \
		echo "Usage: make capture-receipts SUBSYSTEM=<name> OUT=<path>"; \
		exit 2; \
	fi
	$(PYTHON) scripts/capture_guardrail_receipts.py --subsystem $(SUBSYSTEM) --out $(OUT)
capture-test-receipt:
	@if [ -z "$(OUT)" ]; then \
		echo "Usage: make capture-test-receipt OUT=<path>"; \
		exit 2; \
	fi
	$(PYTHON) scripts/capture_test_receipt.py --out $(OUT)
proof-summary:
	@if [ -z "$(RUN_ID)" ] || [ -z "$(OUT)" ]; then \
		echo "Usage: make proof-summary RUN_ID=<id> OUT=<path>"; \
		exit 2; \
	fi
	$(PYTHON) scripts/summarize_proof_run.py --run-id $(RUN_ID) --out $(OUT)
validate-proof-summary:
	@if [ -z "$(SUMMARY)" ] || [ -z "$(OUT)" ]; then \
		echo "Usage: make validate-proof-summary SUMMARY=<path> OUT=<path>"; \
		exit 2; \
	fi
	$(PYTHON) scripts/validate_proof_operator_summary.py --summary $(SUMMARY) --out $(OUT)
run-mircl-v1:
	@if [ -z "$(REQUEST)" ]; then \
		echo "Usage: make run-mircl-v1 REQUEST=<path>"; \
		exit 2; \
	fi
	$(PYTHON) scripts/run_mircl_v1.py --request $(REQUEST)
run-mbom-v1:
	@if [ -z "$(REQUEST)" ]; then \
		echo "Usage: make run-mbom-v1 REQUEST=<path>"; \
		exit 2; \
	fi
	$(PYTHON) scripts/run_mbom_v1.py --request $(REQUEST)

capture-repo-status:
	@if [ -z "$(OUT)" ]; then \
		echo "Usage: make capture-repo-status OUT=<path>"; \
		exit 2; \
	fi
	$(PYTHON) scripts/capture_repo_status_receipt.py --out $(OUT)
validate-run:
	@if [ -z "$(RUN_ID)" ] || [ -z "$(ARTIFACT_ID)" ] || [ -z "$(LEDGER_RECORD_ID)" ] || [ -z "$(PACKET_ID)" ] || [ -z "$(OUT)" ]; then \
		echo "Usage: make validate-run RUN_ID=<id> ARTIFACT_ID=<id> LEDGER_RECORD_ID=<id> PACKET_ID=<id> OUT=<path>"; \
		exit 2; \
	fi
	$(PYTHON) scripts/validate_run.py --run-id $(RUN_ID) --artifact-id $(ARTIFACT_ID) --ledger-record-id $(LEDGER_RECORD_ID) --packet-id $(PACKET_ID) --out $(OUT)
release-manifest:
	$(PYTHON) .abraxas/scripts/generate_release_manifest.py --out /tmp/release_manifest.json
subsystem-audit:
	$(PYTHON) .abraxas/scripts/generate_subsystem_audit.py --subsystem oracle_signal_layer_v2
governance-summary:
	$(PYTHON) .abraxas/scripts/governance_summary.py
validate-record:
	$(PYTHON) .abraxas/scripts/validate_governance_record.py --record .abraxas/templates/promotion_decision_record.json
reconcile-subsystem:
	$(PYTHON) .abraxas/scripts/reconcile_subsystem_state.py --ledger .abraxas/ledger/promotion_decisions.jsonl
continuity-drift:
	$(PYTHON) .abraxas/scripts/continuity_drift_check.py
repo-status:
	$(PYTHON) .abraxas/scripts/repo_status.py
repo-guardrails: preflight registry-check proof-check governance-lint release-readiness continuity-drift repo-status

test:
	pytest -q tests/test_preflight.py tests/test_check_proof_claims.py tests/test_registry_consistency.py tests/test_release_readiness.py tests/test_governance_lint.py tests/test_append_governance_record.py tests/test_generate_release_manifest.py tests/test_governance_summary.py tests/test_validate_governance_record.py tests/test_reconcile_subsystem_state.py tests/test_continuity_drift_check.py tests/test_repo_status.py tests/test_validate_run.py tests/test_capture_guardrail_receipts.py tests/test_capture_test_receipt.py tests/test_capture_repo_status_receipt.py tests/test_run_proof.py tests/test_mbom_v1.py tests/test_oracle_registry_mbom.py

run-oracle-signal-layer-v2:
	@if [ -z "$(INPUT)" ]; then 		echo "Usage: make run-oracle-signal-layer-v2 INPUT=<path> [REPEATS=<n>] [OUT_DIR=<path>]"; 		exit 2; 	fi
	PYTHONPATH=. $(PYTHON) scripts/run_oracle_signal_layer_v2.py --input $(INPUT) $(if $(REPEATS),--repeats $(REPEATS),) $(if $(OUT_DIR),--out-dir $(OUT_DIR),)

run-oracle-signal-layer-v2-invariance:
	@if [ -z "$(INPUT)" ]; then 		echo "Usage: make run-oracle-signal-layer-v2-invariance INPUT=<path> [REPEATS=<n>] [OUT=<path>]"; 		exit 2; 	fi
	PYTHONPATH=. $(PYTHON) scripts/run_oracle_signal_layer_v2_invariance.py --input $(INPUT) $(if $(REPEATS),--repeats $(REPEATS),) $(if $(OUT),--out $(OUT),)

test-oracle-signal-layer-v2:
	PYTHONPATH=. pytest -q tests/oracle/test_schema_guard.py tests/oracle/test_not_computable_flow.py tests/oracle/test_invariance_digests.py tests/oracle/test_advisory_boundaries.py tests/oracle/test_validator_summary.py tests/test_oracle_signal_layer_v2_drop.py tests/test_webpanel_oracle_signal_artifact_viewer.py

