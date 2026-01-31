/**
 * ABX-Core v1.2 - Watchlist Scorer Pipeline
 * SEED Framework Compliant
 *
 * @module abraxas/pipelines/watchlist-scorer
 * @entropy_class medium
 * @deterministic true
 * @capabilities { read: ["weights", "features", "indicators"], write: ["scores"], network: false }
 *
 * Refactored watchlist scoring pipeline integrating:
 * - Symbolic metrics kernel
 * - Archetype resonance
 * - ABX-Runes IR
 * - Deterministic feature extraction
 */

import type { RitualInput, RitualContext } from "../models/ritual";
import type { OracleResult, WatchlistOracleOutput } from "../models/oracle";
import type { FeatureVector, ScoredVector } from "../models/vector";
import type { SymbolicMetrics } from "../core/kernel";

import { aggregateQualityScore, type SymbolicVector } from "../core/kernel";
import { computeSymbolicMetricsOptimized } from "../core/kernel-optimized";
import { mapToArchetype, computeArchetypeResonance, ARCHETYPES } from "../core/archetype";
import { ritualToContext, createFeatureVector } from "../integrations/runes-adapter";
import { evalDynamicIndicators } from "../../indicators";

// Import legacy feature generation (to be refactored further)
import crypto from "crypto";

// ═══════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const DEFAULT_WEIGHTS = {
  nightlights_z: 0.8,
  port_dwell_delta: -0.6,
  sam_mod_scope_delta: 0.9,
  ptab_ipr_burst: -0.7,
  fr_waiver_absence: 0.4,
  jobs_clearance_burst: 0.5,
  hs_code_volume_z: 0.6,
  fx_basis_z: -0.4,
  numerology_reduced: 0.08,
  numerology_master: 0.12,
  gematria_alignment: 0.1,
  astro_rul_align: 0.1,
  astro_waxing: 0.05,
};

let CURRENT_WEIGHTS: Record<string, number> = { ...DEFAULT_WEIGHTS };

export function getWeights() {
  return { ...CURRENT_WEIGHTS };
}

export function setWeights(next: Record<string, number>) {
  const w: Record<string, number> = { ...CURRENT_WEIGHTS };
  for (const k of Object.keys(next || {})) {
    const allow = k in DEFAULT_WEIGHTS || k.startsWith("ind:");
    const v = next[k];
    if (allow && typeof v === "number" && isFinite(v) && Math.abs(v) <= 5) {
      w[k] = +v;
    }
  }
  CURRENT_WEIGHTS = w;
  return getWeights();
}

// ═══════════════════════════════════════════════════════════════════════════
// Feature Extraction (Legacy, to be modularized)
// ═══════════════════════════════════════════════════════════════════════════

function hseed(str: string): number {
  return parseInt(crypto.createHash("sha256").update(str).digest("hex").slice(0, 8), 16);
}

function demoFeaturesForTicker(ticker: string, seed: string): Record<string, number> {
  const r = (x: string) => ((hseed(ticker + x + seed) % 200) - 100) / 50;
  return {
    nightlights_z: r("nl") / 2,
    port_dwell_delta: r("pd") / 3,
    sam_mod_scope_delta: Math.max(0, r("sam")),
    ptab_ipr_burst: r("ipr") / 4,
    fr_waiver_absence: r("fr") > 0 ? 1 : 0,
    jobs_clearance_burst: r("jobs") > 0.5 ? 1 : 0,
    hs_code_volume_z: r("hs") / 2,
  };
}

function demoFeaturesForPair(pair: string, seed: string): Record<string, number> {
  const r = (x: string) => ((hseed(pair + x + seed) % 200) - 100) / 50;
  return {
    fx_basis_z: r("basis") / 2,
    port_dwell_delta: r("port") / 3,
    hs_code_volume_z: r("hs") / 2,
    nightlights_z: r("nl") / 3,
  };
}

function esotericFeatures({
  name,
  sector,
  now,
}: {
  name: string;
  sector: string;
  now: Date;
}): Record<string, number> {
  const nameHash = hseed(name);
  const dayOfYear = Math.floor(
    (now.getTime() - new Date(now.getFullYear(), 0, 0).getTime()) / (1000 * 60 * 60 * 24)
  );

  const numerology_reduced = (nameHash % 9) + 1;
  const numerology_master = [11, 22, 33].includes(numerology_reduced) ? 1 : 0;
  const gematria_alignment = Math.sin(nameHash / 100) * 0.5;
  const astro_rul_align = Math.cos((dayOfYear + nameHash) / 30) * 0.3;
  const moonPhase = (dayOfYear % 29.5) / 29.5;
  const astro_waxing = moonPhase < 0.5 ? moonPhase * 2 : (1 - moonPhase) * 2;

  return {
    numerology_reduced: numerology_reduced / 9,
    numerology_master,
    gematria_alignment,
    astro_rul_align,
    astro_waxing,
  };
}

function parseRitualDate(date: string): Date {
  const parsed = Date.parse(date);
  return Number.isNaN(parsed) ? new Date(0) : new Date(parsed);
}

function sectorGuess(t: string): string {
  if (/(LMT|NOC|RTX|GD|BA)/.test(t)) return "Aerospace & Defense";
  if (/(CVX|XOM|VLO|MPC)/.test(t)) return "Energy";
  if (/(JPM|GS|MS|BAC)/.test(t)) return "Financials";
  if (/(AMGN|PFE|UNH)/.test(t)) return "Healthcare";
  return "Tech";
}

// ═══════════════════════════════════════════════════════════════════════════
// Scoring Logic (Enhanced with Kernel)
// ═══════════════════════════════════════════════════════════════════════════

function scoreEntity(feats: Record<string, number>, w: Record<string, number>): number {
  let s = 0;
  for (const k in feats) {
    s += (w[k] || 0) * (feats[k] ?? 0);
  }
  return s;
}

function applyTransientDelta(
  base: Record<string, number>,
  fmap: string[],
  delta: number
): Record<string, number> {
  const w: Record<string, number> = { ...base };
  fmap.forEach((f) => {
    if (w[f] !== undefined) {
      w[f] = +(w[f] + delta).toFixed(4);
    }
  });
  return w;
}

async function scoreEquity(
  ticker: string,
  context: RitualContext,
  weights: Record<string, number>
): Promise<ScoredVector> {
  // Extract features
  const baseFeats = demoFeaturesForTicker(ticker, context.seed);
  const sector = sectorGuess(ticker);
  const ritualDate = parseRitualDate(context.date);
  const esoteric = esotericFeatures({ name: ticker, sector, now: ritualDate });
  const dyn = await evalDynamicIndicators(ticker, { date: context.date, seed: context.seed });

  const merged = { ...baseFeats, ...esoteric, ...dyn };

  // Create feature vector
  const vector: FeatureVector = createFeatureVector(ticker, "equity", merged, context);

  // Compute symbolic metrics
  const symbolicVector: SymbolicVector = {
    features: merged,
    timestamp: context.timestamp,
    seed: context.seed,
  };

  const kernelContext = {
    seed: context.seed,
    date: context.date,
    runes: context.runes,
  };

  const symbolicMetrics = computeSymbolicMetricsOptimized(symbolicVector, kernelContext);
  const qualityScore = aggregateQualityScore(symbolicMetrics);

  // Compute archetype alignment
  const archetype = mapToArchetype(ticker, merged, context.seed);
  const archetypeResonance = computeArchetypeResonance(merged, archetype);

  // Traditional scoring
  const edge = +scoreEntity(merged, weights).toFixed(3);

  // Enhanced confidence with symbolic metrics
  const baseConf = Math.max(
    0.1,
    Math.min(
      0.95,
      Math.abs(edge) / 3 + 0.05 * esoteric.numerology_master + 0.05 * esoteric.gematria_alignment
    )
  );

  // Modulate confidence with quality score and archetype resonance
  const confidence = +(
    baseConf * 0.7 +
    qualityScore * 0.2 +
    (archetypeResonance + 1) / 2 * 0.1
  ).toFixed(2);

  // Risk classification
  const risk =
    edge > 0
      ? 1 / (1 + baseFeats.ptab_ipr_burst ** 2)
      : 1.15 + Math.max(0, baseFeats.ptab_ipr_burst);

  return {
    ...vector,
    score: edge,
    confidence,
    riskClass: risk < 1 ? "low" : "high",
    symbolicMetrics,
    qualityScore,
  };
}

async function scoreFX(
  pair: string,
  context: RitualContext,
  weights: Record<string, number>
): Promise<ScoredVector> {
  const baseFeats = demoFeaturesForPair(pair, context.seed);
  const base = pair.slice(0, 3);
  const quote = pair.slice(3);
  const ritualDate = parseRitualDate(context.date);
  const eBase = esotericFeatures({ name: base, sector: "Financials", now: ritualDate });
  const eQuote = esotericFeatures({ name: quote, sector: "Financials", now: ritualDate });
  const eTilt =
    eBase.astro_rul_align - eQuote.astro_rul_align + 0.05 * (eBase.numerology_master - eQuote.numerology_master);

  const dyn = await evalDynamicIndicators(pair, { date: context.date, seed: context.seed });

  const merged = { ...baseFeats, astro_rul_align: eTilt, gematria_alignment: 0, ...dyn };

  const vector: FeatureVector = createFeatureVector(pair, "fx", merged, context);

  const symbolicVector: SymbolicVector = {
    features: merged,
    timestamp: context.timestamp,
    seed: context.seed,
  };

  const kernelContext = {
    seed: context.seed,
    date: context.date,
    runes: context.runes,
  };

  const symbolicMetrics = computeSymbolicMetricsOptimized(symbolicVector, kernelContext);
  const qualityScore = aggregateQualityScore(symbolicMetrics);

  const edge = +scoreEntity(merged, weights).toFixed(3);
  const baseConf = Math.max(0.1, Math.min(0.95, Math.abs(edge) / 3 + Math.max(0, eTilt) / 3));
  const confidence = +(baseConf * 0.7 + qualityScore * 0.3).toFixed(2);

  return {
    ...vector,
    score: edge,
    confidence,
    symbolicMetrics,
    qualityScore,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Main Pipeline
// ═══════════════════════════════════════════════════════════════════════════

export async function scoreWatchlists(
  { equities = [], fx = [] }: { equities?: string[]; fx?: string[] },
  ritual: RitualInput
): Promise<WatchlistOracleOutput> {
  const context = ritualToContext(ritual);
  let weights: Record<string, number> = { ...CURRENT_WEIGHTS };

  // Apply transient deltas from ritual
  if (ritual.deltas) {
    ritual.deltas.forEach(({ feature_map, delta }) => {
      weights = applyTransientDelta(weights, feature_map, delta);
    });
  }

  // Score equities
  const eqVectors = await Promise.all(equities.map((ticker) => scoreEquity(ticker, context, weights)));

  const sortedEq = [...eqVectors].sort((a, b) => b.score - a.score);
  const conservative = sortedEq.filter((x) => x.confidence >= 0.6).slice(0, 6);
  const risky = sortedEq.filter((x) => !conservative.includes(x)).slice(0, 6);

  // Score FX
  const fxVectors = await Promise.all(fx.map((pair) => scoreFX(pair, context, weights)));

  const sortedFx = [...fxVectors].sort((a, b) => b.score - a.score);
  const conservativeFx = sortedFx.filter((x) => x.confidence >= 0.65).slice(0, 4);
  const riskyFx = sortedFx.filter((x) => !conservativeFx.includes(x)).slice(0, 4);

  // Convert to OracleResult format
  const toOracleResult = (v: ScoredVector): OracleResult => ({
    ticker: v.type === "equity" ? v.subject : undefined,
    pair: v.type === "fx" ? v.subject : undefined,
    sector: v.type === "equity" ? sectorGuess(v.subject) : undefined,
    edge: v.score,
    confidence: v.confidence,
    riskClass: v.riskClass,
    features: v.features,
    symbolicMetrics: v.symbolicMetrics,
    qualityScore: v.qualityScore,
  });

  // Compute metadata
  const allVectors = [...eqVectors, ...fxVectors];
  const avgQualityScore =
    allVectors.reduce((sum, v) => sum + (v.qualityScore || 0), 0) / Math.max(1, allVectors.length);

  return {
    equities: {
      conservative: conservative.map(toOracleResult),
      risky: risky.map(toOracleResult),
    },
    fx: {
      conservative: conservativeFx.map(toOracleResult),
      risky: riskyFx.map(toOracleResult),
    },
    metadata: {
      totalProcessed: equities.length + fx.length,
      avgQualityScore: +avgQualityScore.toFixed(3),
      timestamp: context.timestamp,
    },
  };
}
