import { AliveMetricProposal } from "@shared/alive/metric-proposals";

export type ProposalStatus =
  | "queued"
  | "approved"
  | "rejected"
  | "in_shadow"
  | "needs_more_data"
  | "ready_to_promote"
  | "promoted"
  | "deprecated";

export interface ProposalRecord {
  proposal_id: string;
  created_at: string;
  updated_at: string;
  status: ProposalStatus;
  proposal: AliveMetricProposal;
  owner?: string;
  notes?: string[];
  eval?: {
    last_evaluated_at?: string;
    shadow_runs?: number;
    stability_score?: number;
    utility_score?: number;
    failure_score?: number;
    promotion_score?: number;
    blockers?: string[];
  };
}

export interface ProposalStore {
  upsert(record: ProposalRecord): Promise<void>;
  get(proposal_id: string): Promise<ProposalRecord | null>;
  list(status?: ProposalStatus): Promise<ProposalRecord[]>;
}
