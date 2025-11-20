/**
 * ABX-Core v1.2 - Daily Oracle Pipeline
 * SEED Framework Compliant
 *
 * @module abraxas/pipelines/daily-oracle
 * @entropy_class medium
 * @deterministic true (given seed)
 * @capabilities { read: ["metrics"], write: [], network: false }
 *
 * Synthesizes daily oracle ciphergrams using:
 * - Symbolic kernel metrics
 * - Archetype resonance
 * - Metrics snapshot
 * - Runic influences
 */

import crypto from "crypto";
import type { RitualInput } from "../models/ritual";
import type { FeatureVector } from "../models/vector";
import { computeSymbolicMetrics, aggregateQualityScore } from "../core/kernel";
import { ritualToContext, createPipelineVector } from "../integrations/runes-adapter";
import { selectArchetypesForRunes } from "../core/archetype";

export interface OracleSnapshot {
  sources: number;
  signals: number;
  predictions: number;
  accuracy: number | null;
}

export interface DailyOracleResult {
  ciphergram: string;
  tone: "ascending" | "tempered" | "probing" | "descending";
  litany: string;
  analysis: {
    quality: number;
    drift: number;
    entropy: number;
    resonance: number;
    confidence: number;
  };
  archetypes: string[];
  timestamp: number;
  provenance: {
    seed: string;
    runes: string[];
    metrics: {
      SDR: number;
      MSI: number;
      ARF: number;
      Hσ: number;
    };
  };
}

/**
 * Generate daily oracle ciphergram with symbolic analysis
 */
export function generateDailyOracle(
  ritual: RitualInput,
  metricsSnapshot: OracleSnapshot
): DailyOracleResult {
  const context = ritualToContext(ritual);

  // Create feature vector from metrics snapshot
  const features = {
    accuracy: metricsSnapshot.accuracy ?? 0.5,
    source_density: Math.min(1, metricsSnapshot.sources / 100),
    signal_density: Math.min(1, metricsSnapshot.signals / 100),
    prediction_volume: Math.min(1, metricsSnapshot.predictions / 50),
  };

  const vector = createPipelineVector(
    features,
    "daily-oracle",
    ritual.seed,
    "pipelines/daily-oracle"
  );

  // Compute symbolic metrics
  const metrics = computeSymbolicMetrics(vector, context);
  const quality = aggregateQualityScore(metrics);

  // Determine tone based on multiple factors
  const baseConfidence = metricsSnapshot.accuracy ?? 0.5;
  const adjustedConfidence = baseConfidence * 0.7 + quality * 0.3;

  const tone = determineTone(adjustedConfidence, metrics.SDR, metrics.Hσ);

  // Select archetypes for runes
  const archetypes = selectArchetypesForRunes(ritual.runes.map((r) => r.id));
  const archetypeNames = archetypes.map((a) => a.name);

  // Generate ciphergram
  const ciphergram = generateCiphergram(ritual, tone, metrics);

  // Generate litany
  const litany = generateLitany(tone, archetypes, metrics);

  return {
    ciphergram,
    tone,
    litany,
    analysis: {
      quality,
      drift: metrics.SDR,
      entropy: metrics.Hσ,
      resonance: metrics.ARF,
      confidence: adjustedConfidence,
    },
    archetypes: archetypeNames,
    timestamp: Date.now(),
    provenance: {
      seed: ritual.seed,
      runes: ritual.runes.map((r) => r.id),
      metrics: {
        SDR: metrics.SDR,
        MSI: metrics.MSI,
        ARF: metrics.ARF,
        Hσ: metrics.Hσ,
      },
    },
  };
}

/**
 * Determine oracle tone from multiple symbolic factors
 */
function determineTone(
  confidence: number,
  drift: number,
  entropy: number
): "ascending" | "tempered" | "probing" | "descending" {
  // High confidence + low drift + low entropy = ascending
  if (confidence > 0.6 && drift < 0.3 && entropy < 0.4) {
    return "ascending";
  }

  // Low confidence + high drift + high entropy = descending
  if (confidence < 0.45 && drift > 0.6 && entropy > 0.6) {
    return "descending";
  }

  // Medium confidence + moderate drift = tempered
  if (confidence > 0.52 && drift < 0.5) {
    return "tempered";
  }

  // Default: probing (uncertainty)
  return "probing";
}

/**
 * Generate ciphergram with deterministic encoding
 */
function generateCiphergram(
  ritual: RitualInput,
  tone: string,
  metrics: any
): string {
  const payload = {
    day: ritual.date,
    tone,
    runes: ritual.runes.map((r) => r.id).join("-"),
    quality: Math.round(aggregateQualityScore(metrics) * 1000) / 1000,
  };

  // Deterministic base64 encoding
  const encoded = Buffer.from(JSON.stringify(payload))
    .toString("base64")
    .replace(/=/g, "");

  // Format as glyph sequence
  const glyph = encoded.match(/.{1,8}/g)?.join("·") || encoded;

  return `⟟Σ ${glyph} Σ⟟`;
}

/**
 * Generate litany based on tone and archetypes
 */
function generateLitany(
  tone: string,
  archetypes: any[],
  metrics: any
): string {
  const toneMessages = {
    ascending: "Vectors converge; clarity emerges.",
    tempered: "Vectors converge; witnesses veiled.",
    probing: "Patterns shift; truth obscured.",
    descending: "Entropy rises; coherence fades.",
  };

  const baseMessage = toneMessages[tone as keyof typeof toneMessages] || toneMessages.probing;

  // Add archetype influence if resonance is strong
  if (Math.abs(metrics.ARF) > 0.5 && archetypes.length > 0) {
    const dominant = archetypes[0].name;
    return `${baseMessage} ${dominant} presides.`;
  }

  return baseMessage;
}

/**
 * Generate oracle seal for verification
 */
export function sealOracle(oracle: DailyOracleResult): string {
  const payload = {
    ciphergram: oracle.ciphergram,
    seed: oracle.provenance.seed,
    runes: oracle.provenance.runes,
    timestamp: oracle.timestamp,
  };

  return crypto
    .createHash("sha256")
    .update(JSON.stringify(payload))
    .digest("hex")
    .substring(0, 16);
}
