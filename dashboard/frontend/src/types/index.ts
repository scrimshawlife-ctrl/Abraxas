export interface ArtifactSummary {
  artifact_id: string;
  type: string;
  timestamp: string;
  size_bytes: number;
  path: string;
}

export interface PhaseAlignment {
  alignment_id: string;
  timestamp_utc: string;
  aligned_phase: string;
  domains: string[];
  alignment_strength: number;
  duration_hours?: number;
  tokens_in_phase: Record<string, string[]>;
}

export interface SynchronicityMap {
  patterns: Array<{
    source_domain: string;
    target_domain: string;
    phase: string;
    lag_hours: number;
    confidence: number;
    observation_count: number;
  }>;
  generated_utc: string;
  provenance_hash: string;
}

export interface OracleBundle {
  run_id: string;
  envelope: any;
  surface: any;
  manifest: any;
}

export interface ResonanceNarrative {
  artifact_id: string;
  headline: string;
  signal_summary: Array<{ label: string; value: any; pointer: string }>;
  what_changed: Array<{ label: string; pointer: string; before: any; after: any; change_description: string }>;
  motifs: Array<{ motif: string; strength: number; pointer: string }>;
  constraints_report: { missing_inputs: string[]; not_computable: string[]; evidence_present: boolean };
}

export interface RitualState {
  active_modulations: Record<string, Record<string, number>>;
  recent_executions: Array<{
    execution_id: string;
    protocol_id: string;
    timestamp_utc: string;
    operator: string;
    effect_magnitude: number;
  }>;
}

export interface TimechainStatus {
  blocks: number;
  integrity: string;
  genesis: string;
  latest_block_hash: string;
}

export interface MetricsSummary {
  total_artifacts: number;
  oracle_runs_24h: number;
  phase_alignments_active: number;
  ritual_executions_24h: number;
  timechain_blocks: number;
}

export interface MetricCardProps {
  title: string;
  value: number;
  icon: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}