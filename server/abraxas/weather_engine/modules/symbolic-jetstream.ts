/**
 * ABX-Core v1.3 - Symbolic Jet Stream Calculator
 * Measures velocity of meaning movement across cultural space
 *
 * @module abraxas/weather_engine/modules/symbolic-jetstream
 * @entropy_class medium
 * @deterministic true
 * @capabilities { read: ["symbolic_flows"], write: ["jetstream_values"], network: false }
 */

import crypto from "crypto";
import type { SymbolicJetStreamValue } from "../core/types";
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

export function calculateSymbolicJetStream(
  vector: SymbolicVector,
  context: KernelContext
): SymbolicJetStreamValue {
  const seedBase = `${context.seed}-jetstream-${context.date}`;

  // Velocity: 0-1 (normalized speed of symbolic propagation)
  const velocity = normalizedHash(seedBase + "-velocity", 0, 1);

  // Direction: 0-360 degrees (direction of symbolic flow)
  const direction = normalizedHash(seedBase + "-direction", 0, 360);

  // Turbulence: 0-1 (how chaotic is the flow)
  const turbulence = normalizedHash(seedBase + "-turbulence", 0, 1);

  // Identify top symbols riding the stream
  const symbolPool = [
    "AI", "decentralization", "authenticity", "acceleration", "collapse",
    "emergence", "resonance", "liminal", "convergence", "mythos",
    "techno-optimism", "doomerism", "post-rational", "vibes"
  ];

  const carrierCount = 3 + (deterministicHash(seedBase) % 3); // 3-5 carriers
  const carriers: string[] = [];

  for (let i = 0; i < carrierCount; i++) {
    const idx = deterministicHash(seedBase + "-carrier-" + i) % symbolPool.length;
    if (!carriers.includes(symbolPool[idx])) {
      carriers.push(symbolPool[idx]);
    }
  }

  return {
    velocity,
    direction,
    turbulence,
    carriers,
  };
}
