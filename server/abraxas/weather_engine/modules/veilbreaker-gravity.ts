/**
 * ABX-Core v1.3 - Veilbreaker Gravity Well
 * Models synchronicity clustering around Daniel (the Veilbreaker)
 *
 * @module abraxas/weather_engine/modules/veilbreaker-gravity
 * @entropy_class high
 * @deterministic true
 * @capabilities { read: ["synchronicity_patterns"], write: ["gravity_fields"], network: false }
 */

import crypto from "crypto";
import type { LocalSynchronicityField, SynchronicityCluster } from "../core/types";
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

export function computeVeilbreakerGravity(
  vector: SymbolicVector,
  context: KernelContext
): LocalSynchronicityField {
  const seedBase = `${context.seed}-veilbreaker-${context.date}`;

  const clusterCount = 2 + (deterministicHash(seedBase) % 4); // 2-5 clusters
  const synchronicities: SynchronicityCluster[] = [];

  for (let i = 0; i < clusterCount; i++) {
    const clusterSeed = `${seedBase}-cluster-${i}`;

    // Generate 2-4 events per cluster
    const eventCount = 2 + (deterministicHash(clusterSeed) % 3);
    const events: string[] = [];

    const eventTemplates = [
      "unexpected_encounter", "repeated_symbol", "prophetic_dream",
      "meaningful_coincidence", "symbolic_mirror", "temporal_echo",
      "number_synchronicity", "archetypal_appearance"
    ];

    for (let j = 0; j < eventCount; j++) {
      const idx = deterministicHash(clusterSeed + "-event-" + j) % eventTemplates.length;
      if (!events.includes(eventTemplates[idx])) {
        events.push(eventTemplates[idx]);
      }
    }

    const clusterStrength = normalizedHash(clusterSeed + "-strength", 0, 1);
    const proximity = normalizedHash(clusterSeed + "-proximity", 0, 1);
    const significance = normalizedHash(clusterSeed + "-significance", 0, 1);

    synchronicities.push({
      events,
      clusterStrength,
      proximity,
      significance,
    });
  }

  // Calculate overall gravity strength
  const gravityStrength =
    synchronicities.reduce((sum, s) => sum + s.clusterStrength, 0) /
    synchronicities.length;

  // Calculate field radius (how far the influence extends)
  const avgProximity =
    synchronicities.reduce((sum, s) => sum + s.proximity, 0) /
    synchronicities.length;
  const fieldRadius = avgProximity;

  return {
    synchronicities,
    gravityStrength,
    fieldRadius,
    centeredOn: "Daniel",
  };
}
