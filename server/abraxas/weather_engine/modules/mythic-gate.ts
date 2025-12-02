/**
 * ABX-Core v1.3 - Mythic Gate Index
 * Rates strength of archetypes: trickster, hero, witness, scapegoat, oracle, sovereign
 *
 * @module abraxas/weather_engine/modules/mythic-gate
 * @entropy_class medium
 * @deterministic true
 * @capabilities { read: ["archetypal_patterns"], write: ["gate_index"], network: false }
 */

import crypto from "crypto";
import type { ArchetypeGateIndex, ArchetypeGate } from "../core/types";
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

export function computeMythicGateIndex(
  vector: SymbolicVector,
  context: KernelContext
): ArchetypeGateIndex {
  const archetypeTypes = [
    "trickster", "hero", "witness", "scapegoat", "oracle", "sovereign"
  ] as const;

  const archetypes: ArchetypeGate[] = archetypeTypes.map((type) => {
    const seedBase = `${context.seed}-gate-${type}-${context.date}`;

    const strength = normalizedHash(seedBase + "-strength", 0, 1);
    const openness = normalizedHash(seedBase + "-openness", 0, 1);
    const resonance = normalizedHash(seedBase + "-resonance", 0, 1);

    return {
      type,
      strength,
      openness,
      resonance,
    };
  });

  // Find dominant archetype
  const sortedArchetypes = [...archetypes].sort((a, b) => b.strength - a.strength);
  const dominantArchetype = sortedArchetypes[0].type;

  // Calculate overall gate strength (average of all gates)
  const gateStrength =
    archetypes.reduce((sum, a) => sum + a.strength, 0) / archetypes.length;

  return {
    archetypes,
    dominantArchetype,
    gateStrength,
  };
}
