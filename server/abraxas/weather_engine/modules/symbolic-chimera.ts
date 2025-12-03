/**
 * ABX-Core v1.3 - Symbolic Chimera Detector
 * Detects hybrid symbolic mutations: blended archetypes, merged narratives
 *
 * @module abraxas/weather_engine/modules/symbolic-chimera
 * @entropy_class high
 * @deterministic true
 * @capabilities { read: ["symbolic_patterns"], write: ["chimera_signals"], network: false }
 */

import crypto from "crypto";
import type { ChimeraSignal, ChimeraEntity } from "../core/types";
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

export function detectSymbolicChimera(
  vector: SymbolicVector,
  context: KernelContext
): ChimeraSignal {
  const archetypes = [
    "warrior", "sage", "fool", "monarch", "trickster",
    "lover", "magician", "innocent", "rebel", "caregiver"
  ];

  // Generate chimera hybrids
  const hybrids: ChimeraEntity[] = [];
  const chimeraCount = 3 + (deterministicHash(context.seed) % 3); // 3-5 chimeras

  for (let i = 0; i < chimeraCount; i++) {
    const seedBase = `${context.seed}-chimera-${i}-${context.date}`;

    // Select 2-3 components for this chimera
    const componentCount = 2 + (deterministicHash(seedBase) % 2);
    const components: string[] = [];

    for (let j = 0; j < componentCount; j++) {
      const idx = deterministicHash(seedBase + j) % archetypes.length;
      if (!components.includes(archetypes[idx])) {
        components.push(archetypes[idx]);
      }
    }

    const strength = normalizedHash(seedBase + "-strength", 0, 1);
    const coherence = normalizedHash(seedBase + "-coherence", 0, 1);

    hybrids.push({
      components,
      strength,
      coherence,
      interpretation: interpretChimera(components, strength, coherence),
    });
  }

  // Calculate overall mutation rate
  const mutationRate = hybrids.reduce((sum, h) => sum + h.strength, 0) / hybrids.length;

  // Calculate stability (inverse of mutation rate, adjusted by coherence)
  const avgCoherence = hybrids.reduce((sum, h) => sum + h.coherence, 0) / hybrids.length;
  const stability = avgCoherence * (1 - mutationRate);

  return {
    hybrids,
    mutationRate,
    stability,
  };
}

function interpretChimera(
  components: string[],
  strength: number,
  coherence: number
): string {
  const joined = components.join("-");
  const level = strength > 0.6 ? "Strong" : strength > 0.3 ? "Emerging" : "Weak";
  const cohesion = coherence > 0.6 ? "stable" : coherence > 0.3 ? "volatile" : "unstable";
  return `${level} ${joined} hybrid (${cohesion})`;
}
