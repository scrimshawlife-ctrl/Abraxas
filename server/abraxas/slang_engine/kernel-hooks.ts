/**
 * ABRAXAS SLANG ENGINE - Kernel Integration Hooks
 * Passive, deterministic integration with ABRAXAS kernel
 *
 * @module abraxas/slang_engine/kernel-hooks
 * @deterministic true
 * @capabilities { read: ["signals", "oracle", "memetic"], write: ["metrics"], network: false }
 */

import type {
  SlangSignal,
  SlangClass,
  NarrativeDebtIndex,
  DriftAlert,
  OracleModulation,
  MemeticPressureTrend,
} from "./schema";
import type { SymbolicMetrics } from "../core/kernel";
import { computePressureMagnitude } from "./signal-processor";

// ═══════════════════════════════════════════════════════════════════════════
// Oracle Modulation
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Adjusts Oracle confidence bands based on slang pressure trends
 * Does NOT change outcomes, only confidence
 *
 * Philosophy: Slang pressure = systemic stress → lower confidence in predictions
 */
export function modulateOracleConfidence(
  oracleMetrics: SymbolicMetrics,
  activeSignals: SlangSignal[]
): OracleModulation {
  // Compute pressure by class
  const classPressures: Record<SlangClass, number> = {
    unspoken_load: 0,
    cognitive_drift: 0,
    ritual_avoidance: 0,
    meaning_inflation: 0,
    status_compression: 0,
    temporal_fugue: 0,
  };

  for (const signal of activeSignals) {
    const pressureMag = computePressureMagnitude(signal.pressure_vector);
    classPressures[signal.class] += pressureMag * signal.signal_strength;
  }

  // Normalize by number of signals per class
  const classCount: Record<SlangClass, number> = {
    unspoken_load: 0,
    cognitive_drift: 0,
    ritual_avoidance: 0,
    meaning_inflation: 0,
    status_compression: 0,
    temporal_fugue: 0,
  };

  activeSignals.forEach((s) => classCount[s.class]++);

  Object.keys(classPressures).forEach((key) => {
    const cls = key as SlangClass;
    if (classCount[cls] > 0) {
      classPressures[cls] /= classCount[cls];
    }
  });

  // Compute confidence adjustment
  // High unspoken_load or cognitive_drift reduces confidence
  const unspokenLoad = classPressures.unspoken_load;
  const cognitiveDrift = classPressures.cognitive_drift;
  const meaningInflation = classPressures.meaning_inflation;

  const confidenceAdjustment =
    -0.05 * unspokenLoad -
    0.03 * cognitiveDrift -
    0.02 * meaningInflation;

  // Clamp to [-0.1, 0.1]
  const clampedAdjustment = Math.max(-0.1, Math.min(0.1, confidenceAdjustment));

  // Compute narrative debt influence (system-level stress)
  const totalPressure = Object.values(classPressures).reduce((sum, p) => sum + p, 0);
  const narrativeDebtInfluence = Math.min(1, totalPressure / 3);

  return {
    signal_class_pressures: classPressures,
    confidence_adjustment: clampedAdjustment,
    narrative_debt_influence: narrativeDebtInfluence,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Drift Alerts
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Generates early warnings when slang class frequency spikes
 */
export function generateDriftAlerts(
  activeSignals: SlangSignal[],
  priorSnapshot?: SlangSignal[]
): DriftAlert[] {
  if (!priorSnapshot || priorSnapshot.length === 0) return [];

  const alerts: DriftAlert[] = [];

  // Count signals by class (current and prior)
  const currentCounts = countByClass(activeSignals);
  const priorCounts = countByClass(priorSnapshot);

  // Detect spikes
  for (const cls of Object.keys(currentCounts) as SlangClass[]) {
    const current = currentCounts[cls];
    const prior = priorCounts[cls] || 0;

    if (prior === 0) continue; // Can't compute percentage if prior is zero

    const percentageIncrease = ((current - prior) / prior) * 100;

    // Alert thresholds
    let severity: DriftAlert["severity"] = "low";
    if (percentageIncrease >= 100) severity = "critical"; // 100%+ increase
    else if (percentageIncrease >= 50) severity = "high";  // 50-99% increase
    else if (percentageIncrease >= 25) severity = "medium"; // 25-49% increase
    else if (percentageIncrease >= 10) severity = "low";    // 10-24% increase
    else continue; // Below threshold, no alert

    const affectedSignals = activeSignals
      .filter((s) => s.class === cls)
      .map((s) => s.id || s.term);

    alerts.push({
      alert_id: `drift-${cls}-${Date.now()}`,
      timestamp: new Date().toISOString(),
      class: cls,
      frequency_spike: percentageIncrease,
      affected_signals: affectedSignals,
      severity,
      recommendation: generateRecommendation(cls, severity),
    });
  }

  return alerts;
}

function countByClass(signals: SlangSignal[]): Record<SlangClass, number> {
  const counts: Record<SlangClass, number> = {
    unspoken_load: 0,
    cognitive_drift: 0,
    ritual_avoidance: 0,
    meaning_inflation: 0,
    status_compression: 0,
    temporal_fugue: 0,
  };

  signals.forEach((s) => counts[s.class]++);
  return counts;
}

function generateRecommendation(
  cls: SlangClass,
  severity: DriftAlert["severity"]
): string {
  const recs: Record<SlangClass, string> = {
    unspoken_load: "Monitor for systemic stress indicators; consider narrative debt analysis",
    cognitive_drift: "Track information processing shifts; validate forecast assumptions",
    ritual_avoidance: "Identify suppressed topics; check for narrative inversion signals",
    meaning_inflation: "Assess semantic stability; consider compression validity",
    status_compression: "Monitor social hierarchy disruptions; update archetype resonance",
    temporal_fugue: "Check temporal coherence metrics; validate time-sensitive predictions",
  };

  const base = recs[cls];
  if (severity === "critical") return `URGENT: ${base}`;
  return base;
}

// ═══════════════════════════════════════════════════════════════════════════
// Narrative Debt Index
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Computes system-level stress from aggregated unspoken_load signals
 */
export function computeNarrativeDebt(
  activeSignals: SlangSignal[]
): NarrativeDebtIndex {
  const unspokenSignals = activeSignals.filter(
    (s) => s.class === "unspoken_load"
  );

  if (unspokenSignals.length === 0) {
    return {
      timestamp: new Date().toISOString(),
      total_unspoken_load: 0,
      system_stress_level: 0,
      critical_signals: [],
      trend: "stable",
    };
  }

  // Aggregate unspoken load
  const totalLoad = unspokenSignals.reduce((sum, s) => {
    const pressureMag = computePressureMagnitude(s.pressure_vector);
    return sum + pressureMag * s.signal_strength;
  }, 0);

  // Normalize to [0, 1]
  const normalizedLoad = Math.min(1, totalLoad / unspokenSignals.length);

  // System stress = normalized load weighted by signal count
  const stressLevel = normalizedLoad * Math.min(1, unspokenSignals.length / 10);

  // Identify critical signals (top 20% by strength)
  const sorted = [...unspokenSignals].sort(
    (a, b) => b.signal_strength - a.signal_strength
  );
  const criticalCount = Math.max(1, Math.ceil(sorted.length * 0.2));
  const criticalSignals = sorted.slice(0, criticalCount);

  // Determine trend (requires historical data; stub for now)
  const trend: NarrativeDebtIndex["trend"] = "stable";

  return {
    timestamp: new Date().toISOString(),
    total_unspoken_load: totalLoad,
    system_stress_level: stressLevel,
    critical_signals: criticalSignals,
    trend,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Memetic Futurecast Integration
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Generates pressure trend forecasts for memetic analysis
 * Uses pressure classes as constraints, NOT terms
 */
export function generateMemeticPressureTrends(
  activeSignals: SlangSignal[],
  forecastHorizonDays: number = 30
): MemeticPressureTrend[] {
  const trends: MemeticPressureTrend[] = [];

  const classes: SlangClass[] = [
    "unspoken_load",
    "cognitive_drift",
    "ritual_avoidance",
    "meaning_inflation",
    "status_compression",
    "temporal_fugue",
  ];

  for (const cls of classes) {
    const classSignals = activeSignals.filter((s) => s.class === cls);

    if (classSignals.length === 0) continue;

    // Compute current pressure
    const currentPressure = classSignals.reduce((sum, s) => {
      const pressureMag = computePressureMagnitude(s.pressure_vector);
      return sum + pressureMag * s.signal_strength;
    }, 0) / classSignals.length;

    // Simple linear extrapolation based on signal growth
    // In a full implementation, this would use time series analysis
    const pressureTrend = [currentPressure];

    // Forecast future pressure (simplified)
    for (let day = 1; day <= forecastHorizonDays; day++) {
      // Assume gradual decay unless boosted
      const decayFactor = Math.exp(-day / 60); // 60-day characteristic time
      const forecastPressure = currentPressure * decayFactor;
      pressureTrend.push(forecastPressure);
    }

    // Find predicted peak (if any)
    const maxPressure = Math.max(...pressureTrend);
    const peakIndex = pressureTrend.indexOf(maxPressure);
    const predictedPeak =
      peakIndex > 0
        ? new Date(Date.now() + peakIndex * 24 * 60 * 60 * 1000).toISOString()
        : undefined;

    trends.push({
      class: cls,
      pressure_trend: pressureTrend,
      forecast_horizon_days: forecastHorizonDays,
      predicted_peak: predictedPeak,
    });
  }

  return trends;
}

// ═══════════════════════════════════════════════════════════════════════════
// ECO (Symbolic Compression Operator) Validation
// ═══════════════════════════════════════════════════════════════════════════

export interface CompressionValidation {
  signal_id: string;
  term: string;
  compression_efficacy: number; // [0,1]
  is_bloated: boolean;
  recommendation: string;
}

/**
 * Validates compression efficacy using ECO principles
 * Flags bloated terms that don't compress effectively
 */
export function validateCompressionEfficacy(
  signals: SlangSignal[]
): CompressionValidation[] {
  return signals.map((signal) => {
    const def = signal.definition;
    const wordCount = def.split(/\s+/).length;
    const charCount = def.length;

    // Compression efficacy heuristics
    const avgWordLength = charCount / wordCount;
    const densityScore = Math.min(1, wordCount / 30); // Ideal: 15-30 words
    const clarityScore = Math.min(1, avgWordLength / 7); // Ideal: 5-7 chars/word

    const efficacy = (densityScore * 0.6) + (clarityScore * 0.4);

    // Bloat detection: too long or too sparse
    const isBloated = charCount > 220 || wordCount < 5 || efficacy < 0.4;

    const recommendation = isBloated
      ? "Consider rewriting for better compression"
      : "Compression meets quality standards";

    return {
      signal_id: signal.id || signal.term,
      term: signal.term,
      compression_efficacy: efficacy,
      is_bloated: isBloated,
      recommendation,
    };
  });
}
