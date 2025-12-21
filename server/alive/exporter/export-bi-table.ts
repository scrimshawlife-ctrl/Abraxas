import { AliveRunResult, AliveMetricValue } from "@shared/alive/schema";

export interface AliveBIRow {
  run_id: string;
  created_at: string;
  tier: string;
  metric_id: string;
  axis: string;
  value: number;
  confidence: number;
  status: string;
  version: string;
}

function rowsFromMetric(run: AliveRunResult, metric: AliveMetricValue): AliveBIRow {
  return {
    run_id: run.provenance.run_id,
    created_at: run.provenance.created_at,
    tier: run.view.tier,
    metric_id: metric.metric_id,
    axis: metric.axis,
    value: metric.value,
    confidence: metric.confidence,
    status: metric.status,
    version: metric.version,
  };
}

export function exportAsBITable(run: AliveRunResult): AliveBIRow[] {
  const rows: AliveBIRow[] = [];
  for (const axis of ["influence", "vitality", "life_logistics"] as const) {
    for (const metric of run.signature[axis] ?? []) {
      rows.push(rowsFromMetric(run, metric));
    }
  }
  return rows;
}
