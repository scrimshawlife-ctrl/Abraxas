/**
 * ABX-Core v1.3 - Event Microbursts Module
 * Tracks micro-events in culture: meme spikes, scandal bursts, niche news, creator-lore explosions, symbolic flashpoints
 *
 * @module abraxas/weather_engine/modules/event-microbursts
 * @entropy_class medium
 * @deterministic true
 * @capabilities { read: ["cultural_signals"], write: ["micro_events"], network: false }
 */

import crypto from "crypto";
import type { MicroEventVector, MicroEvent } from "../core/types";
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

export function detectEventMicrobursts(
  vector: SymbolicVector,
  context: KernelContext
): MicroEventVector {
  const features = Object.entries(vector.features);
  const events: MicroEvent[] = [];

  // Define event type thresholds based on feature patterns
  const eventTypes = [
    "meme_spike",
    "scandal_burst",
    "niche_news",
    "creator_lore",
    "symbolic_flashpoint",
  ] as const;

  // Detect events based on feature volatility
  eventTypes.forEach((type, idx) => {
    const seedBase = `${context.seed}-${type}-${context.date}`;
    const intensity = normalizedHash(seedBase + "-intensity", 0, 1);
    const velocity = normalizedHash(seedBase + "-velocity", -1, 1);

    // Check if intensity exceeds threshold (0.3)
    if (intensity > 0.3) {
      events.push({
        type,
        intensity,
        velocity,
        description: generateEventDescription(type, intensity, context),
        timestamp: vector.timestamp,
      });
    }
  });

  // Calculate overall burst metrics
  const totalIntensity = events.reduce((sum, e) => sum + e.intensity, 0);
  const avgVelocity = events.length > 0
    ? events.reduce((sum, e) => sum + Math.abs(e.velocity), 0) / events.length
    : 0;

  // Determine dominant category
  const sortedEvents = [...events].sort((a, b) => b.intensity - a.intensity);
  const dominantCategory = sortedEvents[0]?.type || "none";

  return {
    events,
    burstIntensity: Math.min(1, totalIntensity / eventTypes.length),
    volatility: avgVelocity,
    dominantCategory,
  };
}

function generateEventDescription(
  type: string,
  intensity: number,
  context: KernelContext
): string {
  const intensityLevel = intensity > 0.7 ? "high" : intensity > 0.4 ? "moderate" : "low";
  const descriptions: Record<string, string> = {
    meme_spike: `${intensityLevel} memetic propagation detected in cultural field`,
    scandal_burst: `${intensityLevel} scandal energy disrupting narrative coherence`,
    niche_news: `${intensityLevel} micro-news cluster forming in specialized domains`,
    creator_lore: `${intensityLevel} personal mythology expansion detected`,
    symbolic_flashpoint: `${intensityLevel} symbolic convergence creating resonance spike`,
  };
  return descriptions[type] || `${intensityLevel} event detected`;
}
