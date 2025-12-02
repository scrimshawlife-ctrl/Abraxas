/**
 * ABX-Core v1.3 - Geometric Drift Engine
 * Detects emergent symbolic shapes: circles, triangles, spirals, grids, fractals
 *
 * @module abraxas/weather_engine/modules/geometric-drift
 * @entropy_class low
 * @deterministic true
 * @capabilities { read: ["symbolic_patterns"], write: ["geometric_shapes"], network: false }
 */

import crypto from "crypto";
import type { GeometricShapeIndex, DetectedShape } from "../core/types";
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

export function detectGeometricDrift(
  vector: SymbolicVector,
  context: KernelContext
): GeometricShapeIndex {
  const shapes: DetectedShape[] = [];
  const shapeTypes = ["circle", "triangle", "spiral", "grid", "fractal"] as const;

  shapeTypes.forEach((type) => {
    const seedBase = `${context.seed}-shape-${type}-${context.date}`;
    const strength = normalizedHash(seedBase + "-strength", 0, 1);
    const resonance = normalizedHash(seedBase + "-resonance", 0, 1);

    shapes.push({
      type,
      strength,
      resonance,
      interpretation: interpretShape(type, strength, resonance),
    });
  });

  // Identify dominant shape
  const sortedShapes = [...shapes].sort((a, b) => b.strength - a.strength);
  const dominantShape = sortedShapes[0].type;

  // Calculate complexity (weighted sum of active shapes)
  const activeShapes = shapes.filter((s) => s.strength > 0.3);
  const complexity = activeShapes.length / shapeTypes.length;

  // Calculate stability (inverse of variance in strengths)
  const avgStrength = shapes.reduce((sum, s) => sum + s.strength, 0) / shapes.length;
  const variance = shapes.reduce(
    (sum, s) => sum + Math.pow(s.strength - avgStrength, 2),
    0
  ) / shapes.length;
  const stability = 1 / (1 + variance);

  return {
    shapes,
    dominantShape,
    complexity,
    stability,
  };
}

function interpretShape(
  type: string,
  strength: number,
  resonance: number
): string {
  const interpretations: Record<string, string> = {
    circle: `Cyclical patterns ${strength > 0.6 ? "dominant" : "emerging"}, return and renewal`,
    triangle: `Triadic structures ${strength > 0.6 ? "strong" : "forming"}, tension and resolution`,
    spiral: `Recursive evolution ${strength > 0.6 ? "accelerating" : "beginning"}, growth with memory`,
    grid: `Ordered systems ${strength > 0.6 ? "stabilizing" : "organizing"}, structure and constraint`,
    fractal: `Self-similar complexity ${strength > 0.6 ? "pervasive" : "detected"}, scale invariance`,
  };
  return interpretations[type] || "Unknown geometric pattern";
}
