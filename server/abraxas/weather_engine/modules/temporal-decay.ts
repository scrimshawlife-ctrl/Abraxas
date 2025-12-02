/**
 * ABX-Core v1.3 - Temporal Decay Weighting
 * Applies half-life to symbols: measures symbolic degradation over time
 *
 * @module abraxas/weather_engine/modules/temporal-decay
 * @entropy_class low
 * @deterministic true
 * @capabilities { read: ["symbolic_history"], write: ["decay_models"], network: false }
 */

import crypto from "crypto";
import type { SymbolicDecayModel, DecayingSymbol } from "../core/types";
import type { SymbolicVector, KernelContext } from "../../core/kernel";

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

export function computeTemporalDecay(
  vector: SymbolicVector,
  context: KernelContext
): SymbolicDecayModel {
  const symbols = [
    "abundance", "crisis", "transformation", "stagnation", "breakthrough",
    "collapse", "emergence", "recursion", "stability", "chaos"
  ];

  const decayingSymbols: DecayingSymbol[] = symbols.map((symbol) => {
    const seedBase = `${context.seed}-decay-${symbol}-${context.date}`;

    // Calculate current strength (starts high, decays over time)
    const initialStrength = normalizedHash(seedBase + "-initial", 0.5, 1);
    const decayFactor = normalizedHash(seedBase + "-factor", 0.8, 0.95);

    // Half-life: time for symbol to reach 50% strength (1-30 days)
    const halfLife = normalizedHash(seedBase + "-halflife", 1, 30);

    // Calculate current strength using exponential decay
    // Assume we're at day 0 for deterministic purposes
    const currentStrength = initialStrength;

    // Time remaining until symbol falls below threshold (10%)
    const threshold = 0.1;
    const timeRemaining = halfLife * Math.log(threshold / currentStrength) / Math.log(0.5);

    return {
      symbol,
      currentStrength,
      halfLife,
      timeRemaining: Math.max(0, timeRemaining),
    };
  });

  // Calculate average half-life
  const averageHalfLife =
    decayingSymbols.reduce((sum, s) => sum + s.halfLife, 0) / decayingSymbols.length;

  // Calculate overall decay rate (inverse of average half-life, normalized)
  const decayRate = 1 / (averageHalfLife / 30); // Normalized to 30-day period

  return {
    symbols: decayingSymbols,
    averageHalfLife,
    decayRate,
  };
}
