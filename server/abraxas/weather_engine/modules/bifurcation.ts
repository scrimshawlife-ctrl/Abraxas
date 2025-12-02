/**
 * ABX-Core v1.3 - Bifurcation Engine
 * Detects two-way narrative splits: either/or moments, fork points
 *
 * @module abraxas/weather_engine/modules/bifurcation
 * @entropy_class high
 * @deterministic true
 * @capabilities { read: ["narrative_flows"], write: ["dual_vectors"], network: false }
 */

import crypto from "crypto";
import type { DualVectorMap, NarrativePath } from "../core/types";
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

export function detectBifurcation(
  vector: SymbolicVector,
  context: KernelContext
): DualVectorMap {
  const seedBase = `${context.seed}-bifurcation-${context.date}`;

  // Generate Path A
  const pathA: NarrativePath = {
    direction: generateDirection(seedBase + "-pathA", context),
    momentum: normalizedHash(seedBase + "-pathA-momentum", 0, 1),
    attractorStrength: normalizedHash(seedBase + "-pathA-attractor", 0, 1),
    keySymbols: generateKeySymbols(seedBase + "-pathA", 3),
  };

  // Generate Path B (divergent)
  const pathB: NarrativePath = {
    direction: generateDirection(seedBase + "-pathB", context),
    momentum: normalizedHash(seedBase + "-pathB-momentum", 0, 1),
    attractorStrength: normalizedHash(seedBase + "-pathB-attractor", 0, 1),
    keySymbols: generateKeySymbols(seedBase + "-pathB", 3),
  };

  // Calculate divergence angle (0-180 degrees)
  const divergenceAngle = normalizedHash(seedBase + "-divergence", 30, 150);

  // Calculate stability (how stable is this fork point)
  const avgAttractor = (pathA.attractorStrength + pathB.attractorStrength) / 2;
  const stability = avgAttractor;

  return {
    pathA,
    pathB,
    divergenceAngle,
    stability,
  };
}

function generateDirection(seed: string, context: KernelContext): string {
  const directions = [
    "technological acceleration",
    "cultural retreat",
    "institutional collapse",
    "grassroots emergence",
    "authoritarian consolidation",
    "distributed coordination",
    "aesthetic revolution",
    "pragmatic adaptation",
  ];
  const idx = deterministicHash(seed) % directions.length;
  return directions[idx];
}

function generateKeySymbols(seed: string, count: number): string[] {
  const symbols = [
    "phoenix", "ouroboros", "crossroads", "mirror", "labyrinth",
    "threshold", "vessel", "flame", "spiral", "keystone",
  ];
  const result: string[] = [];
  for (let i = 0; i < count; i++) {
    const idx = deterministicHash(seed + i) % symbols.length;
    if (!result.includes(symbols[idx])) {
      result.push(symbols[idx]);
    }
  }
  return result;
}
