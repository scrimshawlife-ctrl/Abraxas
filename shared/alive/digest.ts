import { AliveTier, AliveRunResult } from "./schema";

export type AliveWindow = "7d" | "30d" | "90d";

export interface AliveTrendPoint {
  timestamp: string;
  value: number;
  confidence?: number;
}

export interface AliveMetricTrend {
  metric_id: string;
  axis: string;
  window: AliveWindow;
  baseline: { mean: number; stdev: number };
  latest: { value: number; z: number };
  series: AliveTrendPoint[];
}

export interface AliveDigest {
  tier: AliveTier;
  generated_at: string;
  window: AliveWindow;
  scope: {
    org_id?: string;
    team_id?: string;
    campaign_id?: string;
    product_id?: string;
    tags?: string[];
  };
  headline: {
    risk_level: "low" | "medium" | "high";
    summary: string;
    key_drivers: string[];
  };
  alerts: AliveRunResult["view"]["alerts"];
  anomalies: Array<{
    code: string;
    severity: "notice" | "warning" | "critical";
    description: string;
    metrics: string[];
  }>;
  trends: {
    aggregates: AliveMetricTrend[];
    key_metrics: AliveMetricTrend[];
  };
  exports: {
    json_ref?: string;
    bi_table_ref?: string;
  };
}
