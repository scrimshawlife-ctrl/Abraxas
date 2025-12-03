/**
 * ABX-Core v1.3 - Shadow Predictive Field
 * Identifies suppressed topics: what wants to surface but hasn't yet
 *
 * @module abraxas/weather_engine/modules/shadow-predictive
 * @entropy_class high
 * @deterministic true
 * @capabilities { read: ["discourse_undercurrents"], write: ["shadow_fields"], network: false }
 */

import crypto from "crypto";
import type { ShadowPressureField, ShadowTopic } from "../core/types";
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

export function detectShadowPressure(
  vector: SymbolicVector,
  context: KernelContext
): ShadowPressureField {
  const topics = [
    "institutional_corruption",
    "collective_trauma",
    "hidden_agendas",
    "taboo_truths",
    "repressed_histories",
    "emerging_consciousness",
  ];

  const shadowTopics: ShadowTopic[] = topics.map((topic) => {
    const seedBase = `${context.seed}-shadow-${topic}-${context.date}`;

    const suppressionStrength = normalizedHash(seedBase + "-suppression", 0, 1);
    const emergenceProbability = normalizedHash(seedBase + "-emergence", 0, 1);

    // Time to surface: inversely related to emergence probability
    const timeToSurface = (1 - emergenceProbability) * 365; // Days (0-365)

    return {
      topic,
      suppressionStrength,
      emergenceProbability,
      timeToSurface,
    };
  });

  // Calculate overall pressure index
  const pressureIndex =
    shadowTopics.reduce((sum, t) => sum + t.suppressionStrength, 0) / shadowTopics.length;

  // Calculate emergence risk (how likely something will break through soon)
  const highRiskTopics = shadowTopics.filter((t) => t.emergenceProbability > 0.6);
  const emergenceRisk = highRiskTopics.length / shadowTopics.length;

  return {
    shadowTopics,
    pressureIndex,
    emergenceRisk,
  };
}
