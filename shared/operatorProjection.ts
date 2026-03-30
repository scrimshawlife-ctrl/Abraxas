export type LocalPromotionState =
  | "LOCAL_ONLY_COMPLETE"
  | "LOCAL_PROMOTION_READY"
  | "NOT_COMPUTABLE";

export type FederatedReadinessState =
  | "FEDERATED_READY"
  | "FEDERATED_INCOMPLETE"
  | "NOT_COMPUTABLE";

export type PromotionPolicyState =
  | "ALLOWED"
  | "BLOCKED"
  | "WAIVED"
  | "NOT_COMPUTABLE";

export type FederatedEvidenceStateSummary =
  | "ABSENT"
  | "VALID"
  | "PARTIAL"
  | "INCONSISTENT"
  | "MALFORMED"
  | "STALE"
  | "UNKNOWN";

export interface OperatorProjectionSummary {
  schema: "OperatorProjectionSummary.v1";
  run_id: string;
  generated_at: string;
  tier1_local_closure: "PASS" | "INCOMPLETE" | "NOT_COMPUTABLE";
  tier2_local_promotion_state: LocalPromotionState;
  tier25_federated_readiness_state: FederatedReadinessState;
  validator_status: string;
  local_attestation_status: string;
  promotion_attestation_status: string;
  proof_closure_status: "COMPLETE" | "INCOMPLETE" | "NOT_COMPUTABLE";
  federated_evidence_present: boolean;
  federated_evidence_state_summary: FederatedEvidenceStateSummary;
  remote_evidence_packet_count: number;
  federated_inconsistency_flag: boolean;
  promotion_policy_state: PromotionPolicyState;
  promotion_policy_reason_codes: string[];
  promotion_policy_requires_federation: boolean;
  promotion_policy_waived: boolean;
  federated_blockers: string[];
  linkage: {
    has_validator: boolean;
    has_local_attestation: boolean;
    has_promotion_attestation: boolean;
    has_tier1_projection: boolean;
    correlation_pointer_count: number;
    correlation_pointers: string[];
    key_artifact_ids: {
      validator_artifact_id: string;
      tier1_projection_artifact_type: string;
    };
  };
  artifacts: {
    validator: string;
    local_attestation: string;
    promotion_attestation: string;
    tier1_projection: string;
  };
  provenance: {
    source: string;
    note: string;
  };
}

export interface EvidenceView {
  run_id: string;
  federated_evidence_state_summary: FederatedEvidenceStateSummary;
  remote_evidence_packet_count: number;
  inconsistency_flag: boolean;
  manifest_validation_outcome: string;
  origin: string;
  packet_list: Array<{
    packet_id: string;
    status: string;
    observed_at: string;
    source: string;
    origin: string;
  }>;
  blockers: string[];
}

export interface ReleaseReadinessView {
  run_id: string;
  status: "READY" | "NOT_READY" | "PARTIAL" | string;
  blocking_issues: string[];
  non_blocking_issues: string[];
  checklist: Array<{
    name: string;
    outcome: string;
    ok: boolean;
    notes: string;
  }>;
}

export interface RunSummaryView {
  run_id: string;
  projection_summary: OperatorProjectionSummary;
  policy_state: PromotionPolicyState | string;
  readiness_state: {
    status: string;
    local_promotion_state: LocalPromotionState | string;
    federated_readiness_state: FederatedReadinessState | string;
  };
  federated_summary: {
    federated_evidence_state_summary: FederatedEvidenceStateSummary;
    remote_evidence_packet_count: number;
    inconsistency_flag: boolean;
    manifest_validation_outcome: string;
  };
  execution_status: {
    status: string;
    overall_status: string;
    policy_decision_state: string;
    fail_reasons: string[];
    artifact: string;
  };
  blockers: string[];
  artifact_refs: string[];
}

export interface RunDiffSummary {
  run_a: string;
  run_b: string;
  changed_fields: string[];
  policy_delta: {
    from: string;
    to: string;
  };
  readiness_delta: {
    from: Record<string, unknown>;
    to: Record<string, unknown>;
  };
  federated_delta: {
    from: Record<string, unknown>;
    to: Record<string, unknown>;
    new_blockers: string[];
    cleared_blockers: string[];
  };
  execution_delta: {
    from: Record<string, unknown>;
    to: Record<string, unknown>;
  };
}
