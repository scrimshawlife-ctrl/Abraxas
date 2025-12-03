/**
 * ABX-Core v1.3 - Archetypal Crosswinds Engine
 * Detects misalignment between events and archetypes
 *
 * @module abraxas/weather_engine/modules/archetypal-crosswinds
 * @entropy_class high
 * @deterministic true
 * @capabilities { read: ["archetypal_patterns", "events"], write: ["crosswind_vectors"], network: false }
 */

import crypto from "crypto";
import type { CrosswindVector, Crosswind } from "../core/types";
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

export function detectArchetypalCrosswinds(
  vector: SymbolicVector,
  context: KernelContext
): CrosswindVector {
  const archetypes = ["warrior", "sage", "fool", "monarch", "trickster", "oracle"];
  const events = [
    "market_crash", "cultural_shift", "technological_breakthrough",
    "political_upheaval", "social_movement", "environmental_crisis"
  ];

  const crosswinds: Crosswind[] = [];

  // Generate crosswind pairs (archetype misaligned with event)
  for (let i = 0; i < 4; i++) {
    const seedBase = `${context.seed}-crosswind-${i}-${context.date}`;

    const archetypeIdx = deterministicHash(seedBase + "-arch") % archetypes.length;
    const eventIdx = deterministicHash(seedBase + "-event") % events.length;

    const archetype = archetypes[archetypeIdx];
    const event = events[eventIdx];

    const misalignment = normalizedHash(seedBase + "-misalign", 0, 1);
    const friction = normalizedHash(seedBase + "-friction", 0, 1);

    crosswinds.push({
      archetype,
      event,
      misalignment,
      friction,
    });
  }

  // Calculate overall misalignment index
  const misalignmentIndex =
    crosswinds.reduce((sum, c) => sum + c.misalignment, 0) / crosswinds.length;

  // Calculate turbulence (weighted by friction)
  const turbulence =
    crosswinds.reduce((sum, c) => sum + c.misalignment * c.friction, 0) /
    crosswinds.length;

  return {
    crosswinds,
    misalignmentIndex,
    turbulence,
  };
}
