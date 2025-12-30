/**
 * ABX-Core v1.4 - Slang Mutation Model (SLANG Engine Integration)
 * Bridges Weather Engine with SLANG Signal Processing
 *
 * @module abraxas/weather_engine/modules/slang-mutation
 * @entropy_class high
 * @deterministic true
 * @capabilities { read: ["linguistic_patterns"], write: ["slang_forecasts"], network: false }
 */

import crypto from "crypto";
import type { SlangMutationForecast, SlangTerm } from "../core/types";
import type { SymbolicVector, KernelContext } from "../../core/kernel";
import {
  type SlangSignal,
  type SlangClass,
  generatePressureVector,
  computePressureMagnitude,
  applyDecay,
  getDefaultHalfLife,
} from "../../slang_engine";

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

/**
 * Maps SLANG Signal to SlangTerm for backward compatibility
 */
function signalToTerm(signal: SlangSignal, seed: string): SlangTerm {
  const seedBase = `${seed}-slang-${signal.term}`;

  // Map pressure magnitude to viral stability
  const pressureMag = computePressureMagnitude(signal.pressure_vector);
  const viralStability = Math.min(1, pressureMag / 2);

  // Use cognitive + social pressure for drift mobility
  const driftMobility = Math.min(
    1,
    (signal.pressure_vector.cognitive + signal.pressure_vector.social) / 2
  );

  // Mutation probability from signal novelty
  const mutationProbability = signal.novelty ?? normalizedHash(seedBase + "-mutation", 0, 1);

  return {
    term: signal.term,
    mutationProbability,
    driftMobility,
    viralStability,
    semanticHalfLife: signal.decay_halflife_days,
  };
}

/**
 * Generates sample SLANG signals from common terms
 */
function generateSampleSignals(seed: string, date: string): SlangSignal[] {
  const slangTerms = [
    { term: "vibe-check", class: "status_compression" as SlangClass },
    { term: "touch-grass", class: "ritual_avoidance" as SlangClass },
    { term: "brain-rot", class: "cognitive_drift" as SlangClass },
    { term: "cooked", class: "unspoken_load" as SlangClass },
    { term: "locked-in", class: "temporal_fugue" as SlangClass },
    { term: "aura", class: "meaning_inflation" as SlangClass },
    { term: "sigma", class: "status_compression" as SlangClass },
    { term: "mid", class: "meaning_inflation" as SlangClass },
    { term: "lowkey", class: "unspoken_load" as SlangClass },
    { term: "based", class: "status_compression" as SlangClass },
    { term: "cringe", class: "ritual_avoidance" as SlangClass },
    { term: "slay", class: "meaning_inflation" as SlangClass },
  ];

  return slangTerms.map(({ term, class: signalClass }) => {
    const seedBase = `${seed}-${term}-${date}`;
    const pressure_vector = generatePressureVector(term, seedBase);
    const decay_halflife_days = getDefaultHalfLife(signalClass);
    const frequency_index = normalizedHash(seedBase + "-freq", 0.3, 0.9);
    const novelty = normalizedHash(seedBase + "-novelty", 0.4, 0.95);

    // Compute signal strength
    const pressureMag = computePressureMagnitude(pressure_vector);
    const signal_strength = frequency_index * pressureMag * novelty;

    return {
      term,
      class: signalClass,
      definition: `[Generated definition for ${term}]`,
      origin_context: "social_media",
      pressure_vector,
      symptoms: [],
      timestamp_first_seen: new Date(date).toISOString(),
      decay_halflife_days,
      frequency_index,
      signal_strength: Math.min(1, signal_strength / Math.sqrt(5)),
      confidence: normalizedHash(seedBase + "-conf", 0.5, 0.9),
      novelty,
      id: `${term}-${Date.now()}`,
    };
  });
}

/**
 * Forecasts slang mutation using SLANG Engine
 * Maintains backward compatibility with weather engine interface
 */
export function forecastSlangMutation(
  vector: SymbolicVector,
  context: KernelContext
): SlangMutationForecast {
  const seed = `${context.seed}-slang`;

  // Generate SLANG signals
  const signals = generateSampleSignals(context.seed, context.date);

  // Convert to SlangTerm format for backward compatibility
  const terms: SlangTerm[] = signals.map((signal) => signalToTerm(signal, seed));

  // Calculate average mutation rate
  const averageMutationRate =
    terms.reduce((sum, t) => sum + t.mutationProbability, 0) / terms.length;

  // Calculate volatility (variance in drift mobility)
  const avgDrift = terms.reduce((sum, t) => sum + t.driftMobility, 0) / terms.length;
  const variance =
    terms.reduce((sum, t) => sum + Math.pow(t.driftMobility - avgDrift, 2), 0) /
    terms.length;
  const volatility = Math.sqrt(variance);

  return {
    terms,
    averageMutationRate,
    volatility,
  };
}
