/**
 * ABX-Core v1.3 - Forecast Inversion Detector
 * Identifies absences-as-signals: what's NOT being said/shown/discussed
 *
 * @module abraxas/weather_engine/modules/forecast-inversion
 * @entropy_class high
 * @deterministic true
 * @capabilities { read: ["discourse_patterns"], write: ["negative_space"], network: false }
 */

import crypto from "crypto";
import type { NegativeSpaceReading, AbsenceSignal } from "../core/types";
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

export function detectForecastInversion(
  vector: SymbolicVector,
  context: KernelContext
): NegativeSpaceReading {
  // Define expected elements that might be absent
  const expectedElements = [
    "economic_indicators",
    "political_discourse",
    "cultural_critique",
    "technological_progress",
    "social_movements",
    "environmental_concerns",
  ];

  const absences: AbsenceSignal[] = expectedElements.map((element) => {
    const seedBase = `${context.seed}-absence-${element}-${context.date}`;
    const expectedPresence = normalizedHash(seedBase + "-expected", 0.3, 0.9);
    const significance = normalizedHash(seedBase + "-significance", 0, 1);

    return {
      missing: element,
      expectedPresence,
      significance,
      interpretation: interpretAbsence(element, expectedPresence, significance),
    };
  });

  // Calculate suppression index (how much is being hidden)
  const totalExpected = absences.reduce((sum, a) => sum + a.expectedPresence, 0);
  const suppressionIndex = totalExpected / absences.length;

  // Calculate shadow strength (significance of what's missing)
  const shadowStrength =
    absences.reduce((sum, a) => sum + a.significance, 0) / absences.length;

  return {
    absences,
    suppressionIndex,
    shadowStrength,
  };
}

function interpretAbsence(
  element: string,
  expectedPresence: number,
  significance: number
): string {
  const level = significance > 0.6 ? "Critical" : significance > 0.3 ? "Notable" : "Minor";
  return `${level} absence of ${element.replace(/_/g, " ")} (expected ${(expectedPresence * 100).toFixed(0)}%)`;
}
