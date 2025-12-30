/**
 * ABRAXAS SLANG ENGINE - Signal Processor
 * Computes signal strength, pressure magnitudes, and novelty metrics
 *
 * @module abraxas/slang_engine/signal-processor
 * @deterministic true
 * @capabilities { read: ["signals"], write: ["metrics"], network: false }
 */

import crypto from "crypto";
import type {
  SlangSignal,
  PressureVector,
  SignalComputedFields,
} from "./schema";

// ═══════════════════════════════════════════════════════════════════════════
// Hash Utilities (Deterministic)
// ═══════════════════════════════════════════════════════════════════════════

function deterministicHash(input: string): number {
  return parseInt(
    crypto.createHash("sha256").update(input).digest("hex").slice(0, 8),
    16
  );
}

function normalizedHash(input: string, min = 0, max = 1): number {
  const hash = deterministicHash(input);
  return min + ((hash % 10000) / 10000) * (max - min);
}

// ═══════════════════════════════════════════════════════════════════════════
// Pressure Vector Analysis
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Computes the L2 norm (magnitude) of a pressure vector
 * Formula: ||p|| = sqrt(Σ p_i²)
 */
export function computePressureMagnitude(vector: PressureVector): number {
  const sumSquares =
    vector.cognitive ** 2 +
    vector.social ** 2 +
    vector.economic ** 2 +
    vector.temporal ** 2 +
    vector.identity ** 2;

  return Math.sqrt(sumSquares);
}

/**
 * Computes pressure vector from term and seed (deterministic)
 * Used when no manual pressure vector is provided
 */
export function generatePressureVector(
  term: string,
  seed: string
): PressureVector {
  const base = `${seed}-${term}`;

  return {
    cognitive: normalizedHash(`${base}-cognitive`, 0, 1),
    social: normalizedHash(`${base}-social`, 0, 1),
    economic: normalizedHash(`${base}-economic`, 0, 1),
    temporal: normalizedHash(`${base}-temporal`, 0, 1),
    identity: normalizedHash(`${base}-identity`, 0, 1),
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Novelty Computation
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Computes novelty as 1 - semantic_similarity_to_corpus
 * Uses deterministic hashing for corpus comparison
 *
 * In a full implementation, this would use embeddings/cosine similarity
 * For now, we use deterministic hashing as a proxy
 */
export function computeNovelty(
  term: string,
  seed: string,
  existingSignals: SlangSignal[] = []
): number {
  if (existingSignals.length === 0) {
    // First signal is maximally novel
    return 0.95;
  }

  // Compute hash-based similarity to existing corpus
  const termHash = deterministicHash(`${seed}-${term}`);

  const similarities = existingSignals.map((signal) => {
    const signalHash = deterministicHash(`${seed}-${signal.term}`);
    const hashDiff = Math.abs(termHash - signalHash);

    // Normalize hash difference to [0, 1] similarity
    // Lower diff = higher similarity
    const maxHashDiff = 0xffffffff;
    return 1 - Math.min(1, hashDiff / maxHashDiff);
  });

  // Average similarity to corpus
  const avgSimilarity =
    similarities.reduce((sum, s) => sum + s, 0) / similarities.length;

  // Novelty = 1 - similarity
  const novelty = 1 - avgSimilarity;

  // Clamp to reasonable range [0.1, 0.95]
  return Math.max(0.1, Math.min(0.95, novelty));
}

// ═══════════════════════════════════════════════════════════════════════════
// Signal Strength Computation
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Computes signal strength: frequency × pressure_magnitude × novelty
 *
 * This is the core metric for signal quality and relevance
 */
export function computeSignalStrength(
  signal: SlangSignal,
  novelty?: number
): number {
  const pressureMag = computePressureMagnitude(signal.pressure_vector);
  const nov = novelty ?? signal.novelty ?? 0.5;

  const strength = signal.frequency_index * pressureMag * nov;

  // Normalize to [0, 1] range
  // Max theoretical: 1.0 × sqrt(5) × 1.0 ≈ 2.236
  const maxTheoretical = Math.sqrt(5);
  return Math.min(1, strength / maxTheoretical);
}

// ═══════════════════════════════════════════════════════════════════════════
// Unified Signal Computation
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Computes all derived fields for a signal
 */
export function computeSignalFields(
  signal: SlangSignal,
  seed: string,
  existingSignals: SlangSignal[] = []
): SignalComputedFields {
  const pressure_magnitude = computePressureMagnitude(signal.pressure_vector);
  const novelty = computeNovelty(signal.term, seed, existingSignals);
  const signal_strength = signal.frequency_index * pressure_magnitude * novelty;

  // Normalize signal_strength to [0, 1]
  const maxTheoretical = Math.sqrt(5);
  const normalized_strength = Math.min(1, signal_strength / maxTheoretical);

  return {
    pressure_magnitude,
    novelty,
    signal_strength: normalized_strength,
  };
}

/**
 * Updates a signal with computed fields
 */
export function enrichSignal(
  signal: SlangSignal,
  seed: string,
  existingSignals: SlangSignal[] = []
): SlangSignal {
  const computed = computeSignalFields(signal, seed, existingSignals);

  return {
    ...signal,
    novelty: computed.novelty,
    signal_strength: computed.signal_strength,
    last_updated: new Date().toISOString(),
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Frequency Index Computation (Rolling Window)
// ═══════════════════════════════════════════════════════════════════════════

export interface ObservationWindow {
  observations: Array<{
    timestamp: string;
    count: number;
  }>;
  window_days: number;
}

/**
 * Computes frequency index from observation window
 * Returns normalized [0, 1] value based on observation density
 */
export function computeFrequencyIndex(window: ObservationWindow): number {
  if (window.observations.length === 0) return 0;

  const now = Date.now();
  const windowMs = window.window_days * 24 * 60 * 60 * 1000;
  const cutoff = now - windowMs;

  // Filter observations within window
  const recentObs = window.observations.filter(
    (obs) => new Date(obs.timestamp).getTime() >= cutoff
  );

  if (recentObs.length === 0) return 0;

  // Sum counts
  const totalCount = recentObs.reduce((sum, obs) => sum + obs.count, 0);

  // Normalize by window size (assume max of 100 observations per day)
  const maxPossible = window.window_days * 100;
  const frequency = Math.min(1, totalCount / maxPossible);

  return frequency;
}

// ═══════════════════════════════════════════════════════════════════════════
// Confidence Computation (Bayesian)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Computes Bayesian posterior confidence based on:
 * - Number of observations
 * - Signal strength
 * - Time since first seen
 * - Cross-domain appearances
 */
export function computeConfidence(
  signal: SlangSignal,
  observations: number,
  crossDomainCount: number = 1
): number {
  const daysSinceFirst =
    (Date.now() - new Date(signal.timestamp_first_seen).getTime()) /
    (24 * 60 * 60 * 1000);

  // Prior: low confidence (0.3)
  let confidence = 0.3;

  // Update based on observations (more obs = higher confidence)
  const obsBoost = Math.min(0.3, observations / 100);
  confidence += obsBoost;

  // Update based on signal strength
  const strengthBoost = signal.signal_strength * 0.2;
  confidence += strengthBoost;

  // Update based on temporal stability (diminishing returns)
  const timeBoost = Math.min(0.1, daysSinceFirst / 90);
  confidence += timeBoost;

  // Update based on cross-domain appearances
  const domainBoost = Math.min(0.1, (crossDomainCount - 1) * 0.05);
  confidence += domainBoost;

  // Clamp to [0, 1]
  return Math.max(0, Math.min(1, confidence));
}
