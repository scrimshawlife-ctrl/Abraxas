/**
 * ABX-Core v1.3 - Meme Barometric Pressure Engine
 * Rates likelihood of meme stability/mutation/collapse
 *
 * @module abraxas/weather_engine/modules/meme-barometric
 * @entropy_class high
 * @deterministic true
 * @capabilities { read: ["meme_patterns"], write: ["meme_pressure"], network: false }
 */

import crypto from "crypto";
import type { MemeBarometricPressure, MemeReading } from "../core/types";
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

export function computeMemeBarometer(
  vector: SymbolicVector,
  context: KernelContext
): MemeBarometricPressure {
  const memeTemplates = [
    "drake-pointing", "distracted-boyfriend", "wojak", "pepe",
    "galaxy-brain", "two-buttons", "this-is-fine", "doge",
    "npc", "gigachad", "soyjak", "trollface"
  ];

  const memes: MemeReading[] = memeTemplates.map((meme) => {
    const seedBase = `${context.seed}-meme-${meme}-${context.date}`;

    const pressure = normalizedHash(seedBase + "-pressure", 0, 1);
    const confidence = normalizedHash(seedBase + "-confidence", 0.5, 1);

    // Determine likelihood based on pressure
    let likelihood: "stable" | "mutating" | "collapsing";
    if (pressure < 0.3) likelihood = "collapsing";
    else if (pressure < 0.7) likelihood = "mutating";
    else likelihood = "stable";

    return {
      meme,
      pressure,
      likelihood,
      confidence,
    };
  });

  // Calculate overall pressure
  const overallPressure =
    memes.reduce((sum, m) => sum + m.pressure, 0) / memes.length;

  // Determine overall stability
  const collapsingCount = memes.filter((m) => m.likelihood === "collapsing").length;
  const stableCount = memes.filter((m) => m.likelihood === "stable").length;

  let stability: "stable" | "volatile" | "collapsing";
  if (collapsingCount > memes.length * 0.4) stability = "collapsing";
  else if (stableCount > memes.length * 0.5) stability = "stable";
  else stability = "volatile";

  return {
    memes,
    overallPressure,
    stability,
  };
}
