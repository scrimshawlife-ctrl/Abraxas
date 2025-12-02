/**
 * ABX-Core v1.3 - Digital Body Temperature Scanner
 * Measures emotional states: anxiety, irony, sincerity, nostalgia, villain-arc desire, attention volatility
 *
 * @module abraxas/weather_engine/modules/body-temperature
 * @entropy_class medium
 * @deterministic true
 * @capabilities { read: ["affect_signals"], write: ["collective_affect"], network: false }
 */

import crypto from "crypto";
import type { CollectiveAffectProfile, EmotionalState } from "../core/types";
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

export function scanBodyTemperature(
  vector: SymbolicVector,
  context: KernelContext
): CollectiveAffectProfile {
  const emotionTypes = [
    "anxiety",
    "irony",
    "sincerity",
    "nostalgia",
    "villain_arc",
    "attention_volatility",
  ] as const;

  const emotions: EmotionalState[] = emotionTypes.map((type) => {
    const seedBase = `${context.seed}-affect-${type}-${context.date}`;
    const intensity = normalizedHash(seedBase + "-intensity", 0, 1);
    const trendValue = normalizedHash(seedBase + "-trend", 0, 1);

    let trend: "rising" | "stable" | "falling";
    if (trendValue > 0.6) trend = "rising";
    else if (trendValue < 0.4) trend = "falling";
    else trend = "stable";

    return { type, intensity, trend };
  });

  // Find dominant affect
  const sortedEmotions = [...emotions].sort((a, b) => b.intensity - a.intensity);
  const dominantAffect = sortedEmotions[0].type;

  // Calculate volatility (how much emotions are changing)
  const risingCount = emotions.filter((e) => e.trend === "rising").length;
  const fallingCount = emotions.filter((e) => e.trend === "falling").length;
  const volatility = (risingCount + fallingCount) / emotions.length;

  // Calculate temperature (weighted average of intensities)
  const temperature =
    emotions.reduce((sum, e) => sum + e.intensity, 0) / emotions.length;

  return {
    emotions,
    dominantAffect,
    volatility,
    temperature,
  };
}
