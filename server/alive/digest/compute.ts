import type { AliveDigest, AliveMetricTrend, AliveTrendPoint, AliveWindow } from "@shared/alive/digest";
import type { AliveRunResult } from "@shared/alive/schema";
import type { AliveBIRow } from "../exporter/export-bi-table";

const WINDOW_DAYS: Record<AliveWindow, number> = {
  "7d": 7,
  "30d": 30,
  "90d": 90,
};

const KEY_METRICS = ["IM.NCR", "IM.RCF", "IM.RFC", "VM.GI", "LL.LFC"];
const AGGREGATE_METRICS = [
  { id: "influence_intensity", axis: "aggregate" },
  { id: "vitality_charge", axis: "aggregate" },
  { id: "logistics_friction", axis: "aggregate" },
];

function startOfDay(iso: string): string {
  const date = new Date(iso);
  const bucket = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  return bucket.toISOString();
}

function computeStats(values: number[]): { mean: number; stdev: number } {
  if (!values.length) {
    return { mean: 0, stdev: 0 };
  }
  const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
  const variance = values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / values.length;
  return { mean, stdev: Math.sqrt(variance) };
}

function computeTrend(
  metric_id: string,
  axis: string,
  window: AliveWindow,
  series: AliveTrendPoint[]
): AliveMetricTrend {
  const values = series.map((point) => point.value);
  const { mean, stdev } = computeStats(values);
  const latestValue = series.length ? series[series.length - 1].value : 0;
  const denom = stdev < 0.0001 ? 0 : stdev;
  const z = denom === 0 ? 0 : (latestValue - mean) / denom;

  return {
    metric_id,
    axis,
    window,
    baseline: { mean, stdev },
    latest: { value: latestValue, z },
    series,
  };
}

function seriesFromAggregate(runs: AliveRunResult[], key: keyof AliveRunResult["signature"]["aggregates"]): AliveTrendPoint[] {
  const byDay = new Map<string, { sum: number; count: number; confSum: number }>();

  for (const run of runs) {
    const agg = run.signature?.aggregates?.[key];
    if (!agg) continue;
    const day = startOfDay(run.provenance.created_at);
    const entry = byDay.get(day) ?? { sum: 0, count: 0, confSum: 0 };
    entry.sum += agg.value ?? 0;
    entry.count += 1;
    entry.confSum += agg.confidence ?? 0;
    byDay.set(day, entry);
  }

  return Array.from(byDay.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([timestamp, { sum, count, confSum }]) => ({
      timestamp,
      value: count ? sum / count : 0,
      confidence: count ? confSum / count : undefined,
    }));
}

function seriesFromBIRows(rows: AliveBIRow[], metric_id: string): AliveTrendPoint[] {
  const byDay = new Map<string, { sum: number; count: number; confSum: number }>();

  for (const row of rows) {
    if (row.metric_id !== metric_id) continue;
    const day = startOfDay(row.created_at);
    const entry = byDay.get(day) ?? { sum: 0, count: 0, confSum: 0 };
    entry.sum += row.value;
    entry.count += 1;
    entry.confSum += row.confidence;
    byDay.set(day, entry);
  }

  return Array.from(byDay.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([timestamp, { sum, count, confSum }]) => ({
      timestamp,
      value: count ? sum / count : 0,
      confidence: count ? confSum / count : undefined,
    }));
}

function trimSeries(series: AliveTrendPoint[], window: AliveWindow): AliveTrendPoint[] {
  const days = WINDOW_DAYS[window];
  if (!series.length) return series;
  const cutoff = new Date(series[series.length - 1].timestamp);
  cutoff.setUTCDate(cutoff.getUTCDate() - (days - 1));
  return series.filter((point) => new Date(point.timestamp) >= cutoff);
}

function buildAnomalies(trends: AliveMetricTrend[]): AliveDigest["anomalies"] {
  const anomalies: AliveDigest["anomalies"] = [];

  for (const trend of trends) {
    const z = Math.abs(trend.latest.z);
    if (z < 2) continue;

    const severity = z >= 3 ? "critical" : "warning";
    anomalies.push({
      code: `ALIVE.TREND.${trend.metric_id}`,
      severity,
      description: `Trend deviation detected for ${trend.metric_id} (z=${trend.latest.z.toFixed(2)}).`,
      metrics: [trend.metric_id],
    });
  }

  return anomalies;
}

function deriveRiskLevel(
  alerts: AliveRunResult["view"]["alerts"],
  anomalies: AliveDigest["anomalies"]
): AliveDigest["headline"]["risk_level"] {
  const severities = [
    ...(alerts ?? []).map((alert) => alert.severity),
    ...anomalies.map((anomaly) => anomaly.severity),
  ];

  if (severities.includes("critical")) return "high";
  if (severities.includes("warning")) return "medium";
  return "low";
}

export function computeDigest(options: {
  tier: AliveDigest["tier"];
  window: AliveWindow;
  scope?: AliveDigest["scope"];
  runs: AliveRunResult[];
  biRows?: AliveBIRow[];
}): AliveDigest {
  const { tier, window, scope, runs, biRows = [] } = options;

  const aggregateTrends = AGGREGATE_METRICS.map((metric) => {
    const series = trimSeries(seriesFromAggregate(runs, metric.id as keyof AliveRunResult["signature"]["aggregates"]), window);
    return computeTrend(metric.id, metric.axis, window, series);
  });

  const keyMetricTrends = KEY_METRICS.map((metricId) => {
    const series = trimSeries(seriesFromBIRows(biRows, metricId), window);
    const axis = biRows.find((row) => row.metric_id === metricId)?.axis ?? "influence";
    return computeTrend(metricId, axis, window, series);
  });

  const latestRun = runs[runs.length - 1];
  const alerts = latestRun?.view?.alerts ?? [];
  const anomalies = buildAnomalies([...aggregateTrends, ...keyMetricTrends]);
  const riskLevel = deriveRiskLevel(alerts, anomalies);
  const keyDrivers = [
    ...alerts.map((alert) => alert.code),
    ...anomalies.map((anomaly) => anomaly.code),
  ];

  const summary =
    riskLevel === "high"
      ? "High-risk deviations detected; immediate review recommended."
      : riskLevel === "medium"
      ? "Moderate deviation signals present; monitor and validate.";

  return {
    tier,
    generated_at: new Date().toISOString(),
    window,
    scope: scope ?? {},
    headline: {
      risk_level: riskLevel,
      summary: summary ?? "No major deviations detected; steady state.",
      key_drivers: keyDrivers,
    },
    alerts,
    anomalies,
    trends: {
      aggregates: aggregateTrends,
      key_metrics: keyMetricTrends,
    },
    exports: {},
  };
}
