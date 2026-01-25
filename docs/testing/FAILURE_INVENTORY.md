### 1. tests/shadow_metrics/test_access_control.py::test_direct_module_access_blocked
- file: tests/shadow_metrics/test_access_control.py
- nodeid: tests/shadow_metrics/test_access_control.py::test_direct_module_access_blocked
- failure_class: assertion
- suspected_layer: policy
- error_summary: Expected direct module access to raise, but no exception was raised.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 2. tests/test_counterfactual_ledger_chain.py::test_counterfactual_ledger_chain
- file: tests/test_counterfactual_ledger_chain.py
- nodeid: tests/test_counterfactual_ledger_chain.py::test_counterfactual_ledger_chain
- failure_class: exception
- suspected_layer: oracle
- error_summary: yaml.safe_dump fails with RepresenterError when dumping BacktestStatus enum values.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 3. tests/test_counterfactual_report_deltas.py::test_counterfactual_report_deltas
- file: tests/test_counterfactual_report_deltas.py
- nodeid: tests/test_counterfactual_report_deltas.py::test_counterfactual_report_deltas
- failure_class: exception
- suspected_layer: oracle
- error_summary: yaml.safe_dump fails with RepresenterError when dumping BacktestStatus enum values.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 4. tests/test_coupling_lint.py::test_no_direct_rune_imports
- file: tests/test_coupling_lint.py
- nodeid: tests/test_coupling_lint.py::test_no_direct_rune_imports
- failure_class: policy
- suspected_layer: policy
- error_summary: AssertionError listing direct rune imports in server files (../runes).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 5. tests/test_dap_action_selection_online_vs_offline.py::test_dap_action_selection_online_vs_offline
- file: tests/test_dap_action_selection_online_vs_offline.py
- nodeid: tests/test_dap_action_selection_online_vs_offline.py::test_dap_action_selection_online_vs_offline
- failure_class: env
- suspected_layer: operator
- error_summary: FileNotFoundError for tests/fixtures/dap/sample_ledgers/regime_scores.jsonl.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 6. tests/test_dap_gap_detection_from_ledgers.py::test_dap_gap_detection_from_ledgers
- file: tests/test_dap_gap_detection_from_ledgers.py
- nodeid: tests/test_dap_gap_detection_from_ledgers.py::test_dap_gap_detection_from_ledgers
- failure_class: env
- suspected_layer: operator
- error_summary: FileNotFoundError for tests/fixtures/dap/sample_ledgers/forecast_scores.jsonl.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 7. tests/test_dm_metrics.py::test_payload_classification_authentic
- file: tests/test_dm_metrics.py
- nodeid: tests/test_dm_metrics.py::test_payload_classification_authentic
- failure_class: assertion
- suspected_layer: detector
- error_summary: Expected payload type AUTHENTIC but got CONTESTED.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 8. tests/test_dm_metrics.py::test_payload_classification_fabricated
- file: tests/test_dm_metrics.py
- nodeid: tests/test_dm_metrics.py::test_payload_classification_fabricated
- failure_class: assertion
- suspected_layer: detector
- error_summary: Expected payload type FABRICATED but got CONTESTED.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 9. tests/test_drift_log_append_only.py::test_drift_log_appends_on_each_run
- file: tests/test_drift_log_append_only.py
- nodeid: tests/test_drift_log_append_only.py::test_drift_log_appends_on_each_run
- failure_class: assertion
- suspected_layer: oracle
- error_summary: Drift log file not created after running oracle twice.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 10. tests/test_drift_log_append_only.py::test_drift_log_never_overwrites
- file: tests/test_drift_log_append_only.py
- nodeid: tests/test_drift_log_append_only.py::test_drift_log_never_overwrites
- failure_class: assertion
- suspected_layer: oracle
- error_summary: Drift log append/overwrite invariant failure (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 11. tests/test_epp_builds_ranked_proposals.py::test_epp_builds_ranked_proposals
- file: tests/test_epp_builds_ranked_proposals.py
- nodeid: tests/test_epp_builds_ranked_proposals.py::test_epp_builds_ranked_proposals
- failure_class: assertion
- suspected_layer: oracle
- error_summary: Ranked proposals output mismatch or missing (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 12. tests/test_evolution_system.py::test_promotion_creates_ticket
- file: tests/test_evolution_system.py
- nodeid: tests/test_evolution_system.py::test_promotion_creates_ticket
- failure_class: exception
- suspected_layer: oracle
- error_summary: ValueError raised during promotion ticket creation.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 13. tests/test_evolve_ledger_rune.py::test_append_ledger_deterministic_basic
- file: tests/test_evolve_ledger_rune.py
- nodeid: tests/test_evolve_ledger_rune.py::test_append_ledger_deterministic_basic
- failure_class: assertion
- suspected_layer: operator
- error_summary: Deterministic ledger append assertion failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 14. tests/test_evolve_ledger_rune.py::test_append_ledger_determinism
- file: tests/test_evolve_ledger_rune.py
- nodeid: tests/test_evolve_ledger_rune.py::test_append_ledger_determinism
- failure_class: exception
- suspected_layer: operator
- error_summary: KeyError during ledger determinism check.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 15. tests/test_evolve_non_truncation_rune.py::test_enforce_non_truncation_basic
- file: tests/test_evolve_non_truncation_rune.py
- nodeid: tests/test_evolve_non_truncation_rune.py::test_enforce_non_truncation_basic
- failure_class: assertion
- suspected_layer: operator
- error_summary: Non-truncation enforcement assertion failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 16. tests/test_evolve_non_truncation_rune.py::test_enforce_non_truncation_determinism
- file: tests/test_evolve_non_truncation_rune.py
- nodeid: tests/test_evolve_non_truncation_rune.py::test_enforce_non_truncation_determinism
- failure_class: assertion
- suspected_layer: operator
- error_summary: Non-truncation determinism assertion failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 17. tests/test_evolve_non_truncation_rune.py::test_enforce_non_truncation_invalid_inputs
- file: tests/test_evolve_non_truncation_rune.py
- nodeid: tests/test_evolve_non_truncation_rune.py::test_enforce_non_truncation_invalid_inputs
- failure_class: assertion
- suspected_layer: operator
- error_summary: Invalid input handling for non-truncation rune failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 18. tests/test_evolve_non_truncation_rune.py::test_enforce_non_truncation_golden
- file: tests/test_evolve_non_truncation_rune.py
- nodeid: tests/test_evolve_non_truncation_rune.py::test_enforce_non_truncation_golden
- failure_class: assertion
- suspected_layer: operator
- error_summary: Golden output mismatch for non-truncation rune (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 19. tests/test_fdr_attach_components.py::test_fdr_attach_components
- file: tests/test_fdr_attach_components.py
- nodeid: tests/test_fdr_attach_components.py::test_fdr_attach_components
- failure_class: exception
- suspected_layer: oracle
- error_summary: ValueError raised while attaching FDR components.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 20. tests/test_forecast_horizon_rune.py::test_classify_horizon_provenance
- file: tests/test_forecast_horizon_rune.py
- nodeid: tests/test_forecast_horizon_rune.py::test_classify_horizon_provenance
- failure_class: assertion
- suspected_layer: operator
- error_summary: Horizon provenance classification mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 21. tests/test_forecast_horizon_rune.py::test_classify_horizon_determinism
- file: tests/test_forecast_horizon_rune.py
- nodeid: tests/test_forecast_horizon_rune.py::test_classify_horizon_determinism
- failure_class: assertion
- suspected_layer: operator
- error_summary: Horizon classification determinism assertion failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 22. tests/test_influence_synchronicity_flow.py::test_shadow_only_flow_does_not_mutate_prediction_state
- file: tests/test_influence_synchronicity_flow.py
- nodeid: tests/test_influence_synchronicity_flow.py::test_shadow_only_flow_does_not_mutate_prediction_state
- failure_class: assertion
- suspected_layer: detector
- error_summary: Shadow-only flow mutates prediction state or does not match expected state (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 23. tests/test_manifest_integrity.py::TestRegistryReferences::test_definitions_match_manifest
- file: tests/test_manifest_integrity.py
- nodeid: tests/test_manifest_integrity.py::TestRegistryReferences::test_definitions_match_manifest
- failure_class: assertion
- suspected_layer: policy
- error_summary: Registry definitions do not match manifest expectations (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 24. tests/test_manifest_integrity.py::TestRegeneration::test_builder_check_passes
- file: tests/test_manifest_integrity.py
- nodeid: tests/test_manifest_integrity.py::TestRegeneration::test_builder_check_passes
- failure_class: assertion
- suspected_layer: policy
- error_summary: Builder regeneration check failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 25. tests/test_mapping_table_import.py::test_import_mapping_from_csv_row_basic
- file: tests/test_mapping_table_import.py
- nodeid: tests/test_mapping_table_import.py::test_import_mapping_from_csv_row_basic
- failure_class: exception
- suspected_layer: operator
- error_summary: Mapping import from CSV row failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 26. tests/test_mapping_table_import.py::test_import_mapping_from_csv_row_multiple_mri_params
- file: tests/test_mapping_table_import.py
- nodeid: tests/test_mapping_table_import.py::test_import_mapping_from_csv_row_multiple_mri_params
- failure_class: exception
- suspected_layer: operator
- error_summary: Mapping import with multiple MRI params failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 27. tests/test_mapping_table_import.py::test_import_mapping_from_csv_row_empty_params
- file: tests/test_mapping_table_import.py
- nodeid: tests/test_mapping_table_import.py::test_import_mapping_from_csv_row_empty_params
- failure_class: exception
- suspected_layer: operator
- error_summary: Mapping import with empty params failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 28. tests/test_mapping_table_import.py::test_import_mapping_from_csv_row_explanation
- file: tests/test_mapping_table_import.py
- nodeid: tests/test_mapping_table_import.py::test_import_mapping_from_csv_row_explanation
- failure_class: exception
- suspected_layer: operator
- error_summary: Mapping import explanation handling failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 29. tests/test_mapping_table_import.py::test_import_mappings_from_csv
- file: tests/test_mapping_table_import.py
- nodeid: tests/test_mapping_table_import.py::test_import_mappings_from_csv
- failure_class: exception
- suspected_layer: operator
- error_summary: TypeError while importing mappings from CSV.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 30. tests/test_mapping_table_import.py::test_import_mapping_param_descriptions
- file: tests/test_mapping_table_import.py
- nodeid: tests/test_mapping_table_import.py::test_import_mapping_param_descriptions
- failure_class: exception
- suspected_layer: operator
- error_summary: Mapping param descriptions import failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 31. tests/test_mapping_table_import.py::test_import_mapping_null_values
- file: tests/test_mapping_table_import.py
- nodeid: tests/test_mapping_table_import.py::test_import_mapping_null_values
- failure_class: exception
- suspected_layer: operator
- error_summary: Mapping import with null values failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 32. tests/test_memetic_claim_runes.py::test_extract_claim_items_deterministic
- file: tests/test_memetic_claim_runes.py
- nodeid: tests/test_memetic_claim_runes.py::test_extract_claim_items_deterministic
- failure_class: assertion
- suspected_layer: operator
- error_summary: Deterministic claim extraction mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 33. tests/test_memetic_claim_runes.py::test_cluster_claims_deterministic
- file: tests/test_memetic_claim_runes.py
- nodeid: tests/test_memetic_claim_runes.py::test_cluster_claims_deterministic
- failure_class: assertion
- suspected_layer: operator
- error_summary: Deterministic claim clustering mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 34. tests/test_metric_governance.py::test_redundancy_gate_pass_low_correlation
- file: tests/test_metric_governance.py
- nodeid: tests/test_metric_governance.py::test_redundancy_gate_pass_low_correlation
- failure_class: assertion
- suspected_layer: policy
- error_summary: Redundancy gate expected pass at low correlation but failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 35. tests/test_metric_governance.py::test_redundancy_gate_fail_high_correlation
- file: tests/test_metric_governance.py
- nodeid: tests/test_metric_governance.py::test_redundancy_gate_fail_high_correlation
- failure_class: assertion
- suspected_layer: policy
- error_summary: Redundancy gate expected fail at high correlation but did not (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 36. tests/test_metric_governance.py::test_stabilization_gate_fail_high_variance
- file: tests/test_metric_governance.py
- nodeid: tests/test_metric_governance.py::test_stabilization_gate_fail_high_variance
- failure_class: assertion
- suspected_layer: policy
- error_summary: Stabilization gate expected fail at high variance but did not (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 37. tests/test_multi_domain_seedpack.py::test_multi_domain_frame_composition
- file: tests/test_multi_domain_seedpack.py
- nodeid: tests/test_multi_domain_seedpack.py::test_multi_domain_frame_composition
- failure_class: assertion
- suspected_layer: kernel
- error_summary: Multi-domain frame composition mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 38. tests/test_multi_paper_aggregation.py::test_aggregate_mixed_confidence
- file: tests/test_multi_paper_aggregation.py
- nodeid: tests/test_multi_paper_aggregation.py::test_aggregate_mixed_confidence
- failure_class: assertion
- suspected_layer: oracle
- error_summary: Mixed-confidence aggregation assertion failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 39. tests/test_multi_paper_aggregation.py::test_aggregate_single_paper
- file: tests/test_multi_paper_aggregation.py
- nodeid: tests/test_multi_paper_aggregation.py::test_aggregate_single_paper
- failure_class: assertion
- suspected_layer: oracle
- error_summary: Single-paper aggregation assertion failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 40. tests/test_no_regress_guardrail.py::test_no_regress_guardrail
- file: tests/test_no_regress_guardrail.py
- nodeid: tests/test_no_regress_guardrail.py::test_no_regress_guardrail
- failure_class: exception
- suspected_layer: policy
- error_summary: AttributeError raised in no-regress guardrail check.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 41. tests/test_non_censorship_invariant.py::test_static_scan_enforced
- file: tests/test_non_censorship_invariant.py
- nodeid: tests/test_non_censorship_invariant.py::test_static_scan_enforced
- failure_class: assertion
- suspected_layer: policy
- error_summary: Static scan enforcement assertion failed.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 42. tests/test_oracle_mda_bridge_canary.py::test_oracle_bridge_matches_direct_run_slice_hash_evidence_bundle
- file: tests/test_oracle_mda_bridge_canary.py
- nodeid: tests/test_oracle_mda_bridge_canary.py::test_oracle_bridge_matches_direct_run_slice_hash_evidence_bundle
- failure_class: assertion
- suspected_layer: oracle
- error_summary: Oracle bridge run does not match direct run evidence bundle (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 43. tests/test_oracle_mda_bridge_canary.py::test_oracle_bridge_vectors_only_adapter_path_produces_valid_signal
- file: tests/test_oracle_mda_bridge_canary.py
- nodeid: tests/test_oracle_mda_bridge_canary.py::test_oracle_bridge_vectors_only_adapter_path_produces_valid_signal
- failure_class: assertion
- suspected_layer: oracle
- error_summary: Vectors-only adapter path produced invalid signal (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 44. tests/test_oracle_packet_batch.py::test_oracle_batch_emits_packet_and_index
- file: tests/test_oracle_packet_batch.py
- nodeid: tests/test_oracle_packet_batch.py::test_oracle_batch_emits_packet_and_index
- failure_class: assertion
- suspected_layer: oracle
- error_summary: Oracle batch did not emit expected packet and index (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 45. tests/test_oracle_packet_drift.py::test_packet_drift_classifies_shadow_only
- file: tests/test_oracle_packet_drift.py
- nodeid: tests/test_oracle_packet_drift.py::test_packet_drift_classifies_shadow_only
- failure_class: assertion
- suspected_layer: oracle
- error_summary: Packet drift classification for shadow-only mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 46. tests/test_oracle_packet_drift.py::test_packet_drift_classifies_canon
- file: tests/test_oracle_packet_drift.py
- nodeid: tests/test_oracle_packet_drift.py::test_packet_drift_classifies_canon
- failure_class: assertion
- suspected_layer: oracle
- error_summary: Packet drift classification for canon mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 47. tests/test_perf_subsystem.py::TestCompressionRouter::test_compress_decompress_round_trip
- file: tests/test_perf_subsystem.py
- nodeid: tests/test_perf_subsystem.py::TestCompressionRouter::test_compress_decompress_round_trip
- failure_class: assertion
- suspected_layer: transport
- error_summary: Compression/decompression round trip mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 48. tests/test_perf_subsystem.py::TestAcquisitionRunes::test_acquire_bulk_stub
- file: tests/test_perf_subsystem.py
- nodeid: tests/test_perf_subsystem.py::TestAcquisitionRunes::test_acquire_bulk_stub
- failure_class: assertion
- suspected_layer: operator
- error_summary: Bulk acquisition stub behavior mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 49. tests/test_perf_subsystem.py::TestAcquisitionRunes::test_acquire_cache_only_stub
- file: tests/test_perf_subsystem.py
- nodeid: tests/test_perf_subsystem.py::TestAcquisitionRunes::test_acquire_cache_only_stub
- failure_class: assertion
- suspected_layer: operator
- error_summary: Cache-only acquisition stub behavior mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 50. tests/test_perf_subsystem.py::TestAcquisitionRunes::test_acquire_surgical_cap_enforcement
- file: tests/test_perf_subsystem.py
- nodeid: tests/test_perf_subsystem.py::TestAcquisitionRunes::test_acquire_surgical_cap_enforcement
- failure_class: assertion
- suspected_layer: operator
- error_summary: Surgical acquisition cap enforcement mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 51. tests/test_perf_subsystem.py::TestAcquisitionRunes::test_acquire_surgical_requires_reason_code
- file: tests/test_perf_subsystem.py
- nodeid: tests/test_perf_subsystem.py::TestAcquisitionRunes::test_acquire_surgical_requires_reason_code
- failure_class: assertion
- suspected_layer: operator
- error_summary: Surgical acquisition requires reason code assertion failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 52. tests/test_perf_subsystem.py::TestPerfLedger::test_write_perf_event
- file: tests/test_perf_subsystem.py
- nodeid: tests/test_perf_subsystem.py::TestPerfLedger::test_write_perf_event
- failure_class: assertion
- suspected_layer: kernel
- error_summary: Perf ledger event write mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 53. tests/test_runes_invocation.py::test_invoke_logs_stub_blocked
- file: tests/test_runes_invocation.py
- nodeid: tests/test_runes_invocation.py::test_invoke_logs_stub_blocked
- failure_class: assertion
- suspected_layer: policy
- error_summary: Expected invocation to be blocked/logged but it was not (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 54. tests/test_runes_registry.py::test_registry_integrity
- file: tests/test_runes_registry.py
- nodeid: tests/test_runes_registry.py::test_registry_integrity
- failure_class: assertion
- suspected_layer: policy
- error_summary: Rune registry integrity assertion failed.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 55. tests/test_sandbox_portfolio_thresholds.py::test_sandbox_portfolio_thresholds
- file: tests/test_sandbox_portfolio_thresholds.py
- nodeid: tests/test_sandbox_portfolio_thresholds.py::test_sandbox_portfolio_thresholds
- failure_class: assertion
- suspected_layer: oracle
- error_summary: Sandbox portfolio thresholds mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 56. tests/test_score_aggregate_shape.py::test_score_aggregate_shape
- file: tests/test_score_aggregate_shape.py
- nodeid: tests/test_score_aggregate_shape.py::test_score_aggregate_shape
- failure_class: assertion
- suspected_layer: oracle
- error_summary: Score aggregate shape assertion failed.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 57. tests/test_shadow_detectors_bounds.py::test_all_detectors_bounds
- file: tests/test_shadow_detectors_bounds.py
- nodeid: tests/test_shadow_detectors_bounds.py::test_all_detectors_bounds
- failure_class: exception
- suspected_layer: detector
- error_summary: TypeError while validating detector bounds.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 58. tests/test_shadow_detectors_bounds.py::test_mid_range_values
- file: tests/test_shadow_detectors_bounds.py
- nodeid: tests/test_shadow_detectors_bounds.py::test_mid_range_values
- failure_class: exception
- suspected_layer: detector
- error_summary: TypeError while evaluating mid-range detector values.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 59. tests/test_shadow_detectors_determinism.py::test_compliance_remix_determinism
- file: tests/test_shadow_detectors_determinism.py
- nodeid: tests/test_shadow_detectors_determinism.py::test_compliance_remix_determinism
- failure_class: assertion
- suspected_layer: detector
- error_summary: Determinism check failed for compliance_remix detector (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 60. tests/test_shadow_detectors_determinism.py::test_meta_awareness_determinism
- file: tests/test_shadow_detectors_determinism.py
- nodeid: tests/test_shadow_detectors_determinism.py::test_meta_awareness_determinism
- failure_class: assertion
- suspected_layer: detector
- error_summary: Determinism check failed for meta_awareness detector (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 61. tests/test_shadow_detectors_determinism.py::test_negative_space_determinism
- file: tests/test_shadow_detectors_determinism.py
- nodeid: tests/test_shadow_detectors_determinism.py::test_negative_space_determinism
- failure_class: assertion
- suspected_layer: detector
- error_summary: Determinism check failed for negative_space detector (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 62. tests/test_shadow_detectors_determinism.py::test_registry_compute_all_determinism
- file: tests/test_shadow_detectors_determinism.py
- nodeid: tests/test_shadow_detectors_determinism.py::test_registry_compute_all_determinism
- failure_class: assertion
- suspected_layer: detector
- error_summary: Registry compute_all determinism mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 63. tests/test_shadow_detectors_determinism.py::test_sorted_keys_in_output
- file: tests/test_shadow_detectors_determinism.py
- nodeid: tests/test_shadow_detectors_determinism.py::test_sorted_keys_in_output
- failure_class: assertion
- suspected_layer: detector
- error_summary: Output keys not sorted deterministically (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 64. tests/test_shadow_detectors_missing_inputs.py::test_compliance_remix_missing_required_inputs
- file: tests/test_shadow_detectors_missing_inputs.py
- nodeid: tests/test_shadow_detectors_missing_inputs.py::test_compliance_remix_missing_required_inputs
- failure_class: assertion
- suspected_layer: detector
- error_summary: Missing required inputs handling failed for compliance_remix (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 65. tests/test_shadow_detectors_missing_inputs.py::test_compliance_remix_with_all_required_inputs
- file: tests/test_shadow_detectors_missing_inputs.py
- nodeid: tests/test_shadow_detectors_missing_inputs.py::test_compliance_remix_with_all_required_inputs
- failure_class: assertion
- suspected_layer: detector
- error_summary: Required input handling failed for compliance_remix (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 66. tests/test_shadow_detectors_missing_inputs.py::test_negative_space_missing_history
- file: tests/test_shadow_detectors_missing_inputs.py
- nodeid: tests/test_shadow_detectors_missing_inputs.py::test_negative_space_missing_history
- failure_class: assertion
- suspected_layer: detector
- error_summary: Negative space missing history handling failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 67. tests/test_shadow_detectors_missing_inputs.py::test_optional_vs_required_inputs
- file: tests/test_shadow_detectors_missing_inputs.py
- nodeid: tests/test_shadow_detectors_missing_inputs.py::test_optional_vs_required_inputs
- failure_class: assertion
- suspected_layer: detector
- error_summary: Optional vs required inputs handling mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 68. tests/test_shadow_metrics_access_gate.py::test_shadow_lane_allowed_with_sso_rune
- file: tests/test_shadow_metrics_access_gate.py
- nodeid: tests/test_shadow_metrics_access_gate.py::test_shadow_lane_allowed_with_sso_rune
- failure_class: assertion
- suspected_layer: policy
- error_summary: Shadow lane access with SSO rune not allowed as expected (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 69. tests/test_shadow_metrics_access_gate.py::test_prediction_lane_no_sso_required
- file: tests/test_shadow_metrics_access_gate.py
- nodeid: tests/test_shadow_metrics_access_gate.py::test_prediction_lane_no_sso_required
- failure_class: assertion
- suspected_layer: policy
- error_summary: Prediction lane SSO requirement mismatch (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 70. tests/test_sigils_determinism.py::TestRuneDefinitionIntegration::test_load_all_definitions
- file: tests/test_sigils_determinism.py
- nodeid: tests/test_sigils_determinism.py::TestRuneDefinitionIntegration::test_load_all_definitions
- failure_class: assertion
- suspected_layer: kernel
- error_summary: Not all rune definitions loaded deterministically (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 71. tests/test_sim_mappings_game.py::test_game_theoretic_low_discount
- file: tests/test_sim_mappings_game.py
- nodeid: tests/test_sim_mappings_game.py::test_game_theoretic_low_discount
- failure_class: assertion
- suspected_layer: operator
- error_summary: Low-discount game mapping assertion failed (details in pytest output).
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 72. tests/test_sim_mappings_opinion.py::test_opinion_dynamics_full_params
- file: tests/test_sim_mappings_opinion.py
- nodeid: tests/test_sim_mappings_opinion.py::test_opinion_dynamics_full_params
- failure_class: assertion
- suspected_layer: operator
- error_summary: Expected IRI > 0.7 but got 0.2 in opinion dynamics mapping.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 73. tests/test_sim_mappings_opinion.py::test_opinion_dynamics_low_bounded_confidence
- file: tests/test_sim_mappings_opinion.py
- nodeid: tests/test_sim_mappings_opinion.py::test_opinion_dynamics_low_bounded_confidence
- failure_class: assertion
- suspected_layer: operator
- error_summary: Expected IRI > 0.85 but got 0.1 in opinion dynamics mapping.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 74. tests/test_smv_build_units_from_vector_map.py::test_smv_build_units_from_vector_map
- file: tests/test_smv_build_units_from_vector_map.py
- nodeid: tests/test_smv_build_units_from_vector_map.py::test_smv_build_units_from_vector_map
- failure_class: assertion
- suspected_layer: operator
- error_summary: Unit ordering mismatch; expected node IDs before source IDs.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 75. tests/test_smv_computes_ranked_table.py::test_smv_computes_ranked_table
- file: tests/test_smv_computes_ranked_table.py
- nodeid: tests/test_smv_computes_ranked_table.py::test_smv_computes_ranked_table
- failure_class: exception
- suspected_layer: oracle
- error_summary: yaml.safe_dump fails with RepresenterError when dumping BacktestStatus enum values.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED

### 76. tests/test_smv_ledger_chain.py::test_smv_ledger_chain
- file: tests/test_smv_ledger_chain.py
- nodeid: tests/test_smv_ledger_chain.py::test_smv_ledger_chain
- failure_class: exception
- suspected_layer: oracle
- error_summary: yaml.safe_dump fails with RepresenterError when dumping BacktestStatus enum values.
- canon_status: UNCLASSIFIED
- proposed_action: UNCLASSIFIED
