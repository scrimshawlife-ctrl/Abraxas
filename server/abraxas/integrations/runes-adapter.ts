/**
 * ABX-Core v1.2 - ABX-Runes Integration Adapter
 * SEED Framework Compliant
 *
 * @module abraxas/integrations/runes-adapter
 * @deterministic true
 * @capabilities { read: ["runes"], write: [], network: false }
 *
 * Adapts between Abraxas and ABX-Runes IR
 */

import type { Rune, RitualInput, RitualContext } from "../models/ritual";
import type { FeatureVector, VectorProvenance } from "../models/vector";
import type { RuneInvocationContext } from "../runes/ctx.js";

import { invokeRuneByCapability } from "../runes/invoke.js";
import { wiringSanityCheck } from "../runes/registry.js";

export const REQUIRED_RUNE_CAPABILITIES = ["runes:get_today", "runes:run_ritual"];

function assertRequiredCapabilities(): void {
  const sanity = wiringSanityCheck(REQUIRED_RUNE_CAPABILITIES);
  if (sanity.missingCapabilities.length > 0) {
    throw new Error(
      `Missing rune capabilities: ${sanity.missingCapabilities.join(", ")}`
    );
  }
}

/**
 * Initialize ritual from ABX-Runes system
 */
export function initializeRitual(ctx: RuneInvocationContext): RitualInput {
  assertRequiredCapabilities();
  const ritual = invokeRuneByCapability("runes:run_ritual", {}, ctx);

  return {
    date: ritual.date,
    seed: String(ritual.seed),
    runes: ritual.runes as Rune[],
  };
}

/**
 * Get today's runes from ABX-Runes system
 */
export function getTodaysRunes(ctx: RuneInvocationContext): Rune[] {
  assertRequiredCapabilities();
  return invokeRuneByCapability("runes:get_today", {}, ctx) as Rune[];
}

/**
 * Convert Ritual to Context for kernel operations
 */
export function ritualToContext(ritual: RitualInput): RitualContext {
  return {
    seed: ritual.seed,
    date: ritual.date,
    runes: ritual.runes.map((r) => r.id),
    timestamp: Date.now(),
  };
}

/**
 * Create feature vector with provenance tracking
 */
export function createFeatureVector(
  subject: string,
  type: "equity" | "fx",
  features: Record<string, number>,
  context: RitualContext
): FeatureVector {
  const provenance: VectorProvenance = {
    source: "abraxas",
    module: "feature-extraction",
    operation: `generate_${type}_features`,
    generatedAt: Date.now(),
  };

  return {
    id: `${type}-${subject}-${context.seed}-${Date.now()}`,
    type,
    subject,
    features,
    timestamp: context.timestamp,
    seed: context.seed,
    provenance,
  };
}

/**
 * Create feature vector for pipeline operations
 * Generalized version for non-equity/fx subjects
 */
export function createPipelineVector(
  features: Record<string, number>,
  subject: string,
  seed: string,
  module: string
): FeatureVector {
  const provenance: VectorProvenance = {
    source: "abraxas",
    module,
    operation: `generate_features`,
    generatedAt: Date.now(),
  };

  return {
    id: `pipeline-${subject}-${seed}-${Date.now()}`,
    type: "equity", // Generic type for pipeline vectors
    subject,
    features,
    timestamp: Date.now(),
    seed,
    provenance,
  };
}

/**
 * Merge multiple feature vectors with provenance chain
 */
export function mergeVectors(
  vectors: FeatureVector[],
  operation: string
): FeatureVector {
  const merged: Record<string, number> = {};

  vectors.forEach((v) => {
    Object.assign(merged, v.features);
  });

  const provenance: VectorProvenance = {
    source: "abraxas",
    module: "vector-merge",
    operation,
    parentId: vectors.map((v) => v.id).join(","),
    generatedAt: Date.now(),
  };

  return {
    id: `merged-${Date.now()}`,
    type: "aggregate",
    subject: "merged",
    features: merged,
    timestamp: Date.now(),
    seed: vectors[0]?.seed || "",
    provenance,
  };
}
