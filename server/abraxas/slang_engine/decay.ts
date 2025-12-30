/**
 * ABRAXAS SLANG ENGINE - Decay Mechanics
 * Time-based signal degradation, archival, and resurrection
 *
 * @module abraxas/slang_engine/decay
 * @deterministic true
 * @capabilities { read: ["signals"], write: ["archive"], network: false }
 */

import type {
  SlangSignal,
  ArchivedSignal,
  ResurrectionEvent,
  SlangClass,
} from "./schema";
import { DEFAULT_DECAY_PROFILES as DECAY_PROFILES } from "./schema";

// ═══════════════════════════════════════════════════════════════════════════
// Decay Computation
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Computes current signal strength after exponential decay
 * Formula: S(t) = S₀ × e^(-λt)
 * where λ = ln(2) / half_life
 */
export function applyDecay(signal: SlangSignal, currentTime?: number): number {
  const now = currentTime ?? Date.now();
  const firstSeen = new Date(signal.timestamp_first_seen).getTime();
  const ageMs = now - firstSeen;
  const ageDays = ageMs / (24 * 60 * 60 * 1000);

  // Decay constant λ = ln(2) / half_life
  const lambda = Math.log(2) / signal.decay_halflife_days;

  // Exponential decay: S(t) = S₀ × e^(-λt)
  const decayedStrength = signal.signal_strength * Math.exp(-lambda * ageDays);

  return Math.max(0, decayedStrength);
}

/**
 * Checks if signal should be archived based on:
 * 1. Signal strength below threshold for 2 half-lives
 * 2. No recent activity
 */
export function shouldArchive(signal: SlangSignal, currentTime?: number): boolean {
  const now = currentTime ?? Date.now();
  const firstSeen = new Date(signal.timestamp_first_seen).getTime();
  const ageMs = now - firstSeen;
  const ageDays = ageMs / (24 * 60 * 60 * 1000);

  const profile = DECAY_PROFILES[signal.class];
  const twoHalfLives = 2 * signal.decay_halflife_days;

  // Condition 1: Age exceeds 2 half-lives
  if (ageDays < twoHalfLives) return false;

  // Condition 2: Current strength below threshold
  const currentStrength = applyDecay(signal, now);
  if (currentStrength >= profile.archive_threshold) return false;

  return true;
}

/**
 * Archives a signal with metadata
 */
export function archiveSignal(
  signal: SlangSignal,
  reason: string = "Auto-archive: signal strength below threshold for 2 half-lives"
): ArchivedSignal {
  return {
    ...signal,
    archived: true,
    archive_timestamp: new Date().toISOString(),
    archive_reason: reason,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Survival Boosts
// ═══════════════════════════════════════════════════════════════════════════

export interface SurvivalFactors {
  crossDomainAppearances: number;    // Appearances in different contexts
  behavioralCorroboration: boolean;  // Has behavioral evidence
  semanticStability: number;         // [0,1] consistency of meaning
}

/**
 * Computes survival boost multiplier based on factors
 */
export function computeSurvivalBoost(
  signal: SlangSignal,
  factors: SurvivalFactors
): number {
  const profile = DECAY_PROFILES[signal.class];
  let boost = 1.0;

  // Cross-domain boost
  if (factors.crossDomainAppearances > 1) {
    const domainBoost = Math.min(
      profile.survival_boost_multiplier,
      1 + (factors.crossDomainAppearances - 1) * 0.2
    );
    boost *= domainBoost;
  }

  // Behavioral corroboration boost
  if (factors.behavioralCorroboration) {
    boost *= 1.3;
  }

  // Semantic stability boost
  if (factors.semanticStability > 0.7) {
    boost *= 1.2;
  }

  return boost;
}

/**
 * Applies survival boost to a signal's half-life
 */
export function applySurvivalBoost(
  signal: SlangSignal,
  factors: SurvivalFactors
): SlangSignal {
  const boost = computeSurvivalBoost(signal, factors);
  const newHalfLife = signal.decay_halflife_days * boost;

  return {
    ...signal,
    decay_halflife_days: newHalfLife,
    last_updated: new Date().toISOString(),
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Resurrection Logic
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Checks if an archived signal should be resurrected
 * Condition: Resurfaced with ≥60% higher pressure
 */
export function shouldResurrect(
  archivedSignal: ArchivedSignal,
  newPressureMagnitude: number
): boolean {
  // Compute original pressure magnitude
  const originalPressureMag = Math.sqrt(
    archivedSignal.pressure_vector.cognitive ** 2 +
    archivedSignal.pressure_vector.social ** 2 +
    archivedSignal.pressure_vector.economic ** 2 +
    archivedSignal.pressure_vector.temporal ** 2 +
    archivedSignal.pressure_vector.identity ** 2
  );

  // Check for ≥60% increase
  const increasePercent = ((newPressureMagnitude - originalPressureMag) / originalPressureMag) * 100;

  return increasePercent >= 60;
}

/**
 * Resurrects an archived signal with lineage tracking
 */
export function resurrectSignal(
  archivedSignal: ArchivedSignal,
  newSignalStrength: number,
  pressureIncrease: number
): { signal: SlangSignal; event: ResurrectionEvent } {
  const lineageTag = `resurrected-${Date.now()}-from-${archivedSignal.archive_timestamp}`;

  const signal: SlangSignal = {
    ...archivedSignal,
    signal_strength: newSignalStrength,
    timestamp_first_seen: new Date().toISOString(), // Reset to current time
    archived: false,
    lineage: lineageTag,
    last_updated: new Date().toISOString(),
  };

  const event: ResurrectionEvent = {
    signal_id: archivedSignal.id || archivedSignal.term,
    original_term: archivedSignal.term,
    resurrection_timestamp: new Date().toISOString(),
    pressure_increase_percent: pressureIncrease,
    new_signal_strength: newSignalStrength,
    lineage_tag: lineageTag,
  };

  // Remove archive fields
  delete (signal as any).archive_timestamp;
  delete (signal as any).archive_reason;

  return { signal, event };
}

// ═══════════════════════════════════════════════════════════════════════════
// Batch Decay Operations
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Applies decay to all active signals and returns archival candidates
 */
export function processDecayBatch(
  signals: SlangSignal[],
  currentTime?: number
): {
  updated: SlangSignal[];
  toArchive: SlangSignal[];
  decayStats: {
    totalProcessed: number;
    averageDecay: number;
    archivalCount: number;
  };
} {
  const now = currentTime ?? Date.now();
  const updated: SlangSignal[] = [];
  const toArchive: SlangSignal[] = [];
  let totalDecay = 0;

  for (const signal of signals) {
    const originalStrength = signal.signal_strength;
    const decayedStrength = applyDecay(signal, now);
    const decayAmount = originalStrength - decayedStrength;

    totalDecay += decayAmount;

    const updatedSignal = {
      ...signal,
      signal_strength: decayedStrength,
      last_updated: new Date(now).toISOString(),
    };

    if (shouldArchive(updatedSignal, now)) {
      toArchive.push(updatedSignal);
    } else {
      updated.push(updatedSignal);
    }
  }

  return {
    updated,
    toArchive,
    decayStats: {
      totalProcessed: signals.length,
      averageDecay: signals.length > 0 ? totalDecay / signals.length : 0,
      archivalCount: toArchive.length,
    },
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Half-Life Management
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Gets default half-life for a signal class
 */
export function getDefaultHalfLife(signalClass: SlangClass): number {
  return DECAY_PROFILES[signalClass].default_halflife_days;
}

/**
 * Computes adaptive half-life based on signal characteristics
 * Can be longer or shorter than default based on stability
 */
export function computeAdaptiveHalfLife(
  signal: SlangSignal,
  factors: SurvivalFactors
): number {
  const defaultHalfLife = getDefaultHalfLife(signal.class);
  const boost = computeSurvivalBoost(signal, factors);

  return defaultHalfLife * boost;
}
