import { AliveMetricAxis } from "./schema";

export interface AliveMetricProposal {
  proposal_id: string;
  created_at: string;
  working_name: string;
  proposed_metric_id: string;
  candidate_axis: AliveMetricAxis | "cross_axis";
  measures: string;
  motivation: string;
  required_inputs: string[];
  estimation_method: "cue" | "stat" | "hybrid";
  validation_plan: {
    golden_cases: Array<{ label: "high" | "low" | "ambiguous"; notes: string }>;
    failure_modes: string[];
    promotion_criteria: string[];
  };
  tier_copy: {
    psychonaut: { summary: string; prompts?: string[] };
    academic: { summary: string; operational_definition: string; failure_modes?: string[] };
    enterprise: { summary: string; decision_uses?: string[]; business_risk_notes?: string[] };
  };
}
