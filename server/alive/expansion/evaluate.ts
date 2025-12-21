import { ProposalRecord } from "./storage";

export interface EvalInputs {
  metric_series: Array<{ value: number; confidence: number }>;
  golden_fp: number;
  golden_fn: number;
  alert_assoc?: number;
  strain_reduction?: number;
}

function clamp(x: number, lo = 0, hi = 1): number {
  return Math.max(lo, Math.min(hi, x));
}

function mean(values: number[]): number {
  return values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;
}

function variance(values: number[]): number {
  if (values.length < 2) return 0;
  const m = mean(values);
  return values.reduce((a, x) => a + (x - m) * (x - m), 0) / (values.length - 1);
}

export function computeScores(inputs: EvalInputs) {
  const values = inputs.metric_series.map((x) => x.value);
  const confidences = inputs.metric_series.map((x) => x.confidence);

  const varV = variance(values);
  const sat = values.length
    ? values.filter((v) => v < 0.05 || v > 0.95).length / values.length
    : 1;
  const confMean = mean(confidences);

  const targetVar = 0.05;
  const normVar = clamp(varV / targetVar);

  const stability = clamp(0.55 * (1 - normVar) + 0.25 * (1 - sat) + 0.2 * confMean);

  const coverage = values.length ? values.filter((v) => v > 0.1).length / values.length : 0;
  const alertAssoc = clamp(inputs.alert_assoc ?? 0);
  const strainRed = clamp(((inputs.strain_reduction ?? 0) + 1) / 2);

  const utility = clamp(0.45 * coverage + 0.35 * alertAssoc + 0.2 * strainRed);

  const failure = clamp(0.6 * inputs.golden_fp + 0.4 * inputs.golden_fn);

  const promotion = clamp(0.5 * stability + 0.4 * utility - 0.6 * failure);

  return { stability, utility, failure, promotion };
}

export function blockersFor(scores: ReturnType<typeof computeScores>, seriesLen: number): string[] {
  const blockers: string[] = [];
  if (seriesLen < 50) blockers.push("insufficient_shadow_runs(<50)");
  if (scores.stability < 0.6) blockers.push("stability_below_threshold(<0.60)");
  if (scores.utility < 0.55) blockers.push("utility_below_threshold(<0.55)");
  if (scores.failure > 0.2) blockers.push("failure_above_threshold(>0.20)");
  if (scores.promotion < 0.65) blockers.push("promotion_score_below_threshold(<0.65)");
  return blockers;
}

export function updateRecordEvaluation(
  record: ProposalRecord,
  inputs: EvalInputs
): ProposalRecord {
  const scores = computeScores(inputs);
  const blockers = blockersFor(scores, inputs.metric_series.length);
  return {
    ...record,
    eval: {
      last_evaluated_at: new Date().toISOString(),
      shadow_runs: inputs.metric_series.length,
      stability_score: scores.stability,
      utility_score: scores.utility,
      failure_score: scores.failure,
      promotion_score: scores.promotion,
      blockers,
    },
  };
}
