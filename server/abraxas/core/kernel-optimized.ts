/**
 * ABX-Core v1.2 - Optimized Symbolic Kernel
 * SEED Framework Compliant
 *
 * @module abraxas/core/kernel-optimized
 * @entropy_class low
 * @deterministic true
 * @capabilities { read: ["features", "weights", "archetypes", "cache"], write: ["metrics", "cache"], network: false }
 *
 * Performance-optimized wrapper around symbolic kernel with:
 * - Hash result caching
 * - Pre-computed context hashes
 * - Memoized metric calculations
 * - Optimized feature array extractions
 * - Performance monitoring
 */

import crypto from "crypto";
import type {
  SymbolicVector,
  SymbolicMetrics,
  KernelContext,
  KernelDiagnostics,
} from "./kernel";
import {
  computeSDR,
  computeMSI,
  computeARF,
  computeNMC,
  computeRFR,
  computeHσ,
  computeλN,
  computeITC,
  aggregateQualityScore,
} from "./kernel";
import {
  getCachedHash,
  metricCache,
  performanceMonitor,
  extractFeatures,
  type MetricCacheKey,
  type OptimizedFeatures,
} from "./performance";

// ═══════════════════════════════════════════════════════════════════════════
// Optimized Hash Utilities
// ═══════════════════════════════════════════════════════════════════════════

export function deterministicHash(input: string): number {
  return getCachedHash(input, (s: string) =>
    parseInt(
      crypto.createHash("sha256").update(s).digest("hex").slice(0, 8),
      16
    )
  );
}

export function normalizedHash(input: string, min = 0, max = 1): number {
  const hash = deterministicHash(input);
  return min + ((hash % 10000) / 10000) * (max - min);
}

// ═══════════════════════════════════════════════════════════════════════════
// Pre-computed Context Enhancement
// ═══════════════════════════════════════════════════════════════════════════

export interface EnhancedContext extends KernelContext {
  // Pre-computed hash maps
  _runeHashes?: Map<string, number>;
  _archetypeHashes?: Map<string, number>;
  _featureHashCache?: Map<string, number>;
}

export function enhanceContext(context: KernelContext): EnhancedContext {
  const enhanced: EnhancedContext = { ...context };

  // Pre-compute rune hashes
  if (context.runes && context.runes.length > 0) {
    enhanced._runeHashes = new Map();
    context.runes.forEach(rune => {
      enhanced._runeHashes!.set(rune, deterministicHash(rune + context.seed));
    });
  }

  // Pre-compute archetype hashes
  if (context.archetypes && context.archetypes.length > 0) {
    enhanced._archetypeHashes = new Map();
    context.archetypes.forEach(archetype => {
      enhanced._archetypeHashes!.set(archetype, deterministicHash(archetype + context.seed));
    });
  }

  enhanced._featureHashCache = new Map();

  return enhanced;
}

// ═══════════════════════════════════════════════════════════════════════════
// Optimized Metric Computations
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Compute symbolic metrics with caching and performance monitoring
 */
export function computeSymbolicMetricsOptimized(
  vector: SymbolicVector,
  context: KernelContext
): SymbolicMetrics {
  const timer = performanceMonitor.startTimer();

  // Check cache first
  const cacheKey: MetricCacheKey = {
    vectorId: JSON.stringify(vector.features),
    seed: context.seed,
    date: context.date,
  };

  const cached = metricCache.get(cacheKey);
  if (cached !== undefined) {
    timer.end("computeSymbolicMetrics", true);
    return cached;
  }

  // Enhance context for optimized computations
  const enhanced = enhanceContext(context);

  // Compute all metrics
  const metrics: SymbolicMetrics = {
    SDR: computeSDR(vector, enhanced),
    MSI: computeMSI(vector, enhanced),
    ARF: computeARF(vector, enhanced),
    NMC: computeNMC(vector, enhanced),
    RFR: computeRFR(vector, enhanced),
    Hσ: computeHσ(vector, enhanced),
    λN: computeλN(vector, enhanced),
    ITC: computeITC(vector, enhanced),
  };

  // Cache results
  metricCache.set(cacheKey, metrics);

  timer.end("computeSymbolicMetrics", false);
  return metrics;
}

// ═══════════════════════════════════════════════════════════════════════════
// Optimized Feature Extraction
// ═══════════════════════════════════════════════════════════════════════════

export interface VectorWithCache extends SymbolicVector {
  _optimizedFeatures?: OptimizedFeatures;
}

export function optimizeVector(vector: SymbolicVector): VectorWithCache {
  const optimized: VectorWithCache = { ...vector };
  optimized._optimizedFeatures = extractFeatures(vector.features);
  return optimized;
}

// ═══════════════════════════════════════════════════════════════════════════
// Batched Metric Computation
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Compute metrics for multiple vectors in a single batch
 * More efficient than individual computations due to shared context
 */
export function computeMetricsBatch(
  vectors: SymbolicVector[],
  context: KernelContext
): SymbolicMetrics[] {
  const timer = performanceMonitor.startTimer();

  // Enhance context once for all vectors
  const enhanced = enhanceContext(context);

  // Compute metrics for each vector
  const results = vectors.map(vector => {
    const cacheKey: MetricCacheKey = {
      vectorId: JSON.stringify(vector.features),
      seed: context.seed,
      date: context.date,
    };

    const cached = metricCache.get(cacheKey);
    if (cached !== undefined) {
      return cached;
    }

    const metrics: SymbolicMetrics = {
      SDR: computeSDR(vector, enhanced),
      MSI: computeMSI(vector, enhanced),
      ARF: computeARF(vector, enhanced),
      NMC: computeNMC(vector, enhanced),
      RFR: computeRFR(vector, enhanced),
      Hσ: computeHσ(vector, enhanced),
      λN: computeλN(vector, enhanced),
      ITC: computeITC(vector, enhanced),
    };

    metricCache.set(cacheKey, metrics);
    return metrics;
  });

  timer.end("computeMetricsBatch", false);
  return results;
}

// ═══════════════════════════════════════════════════════════════════════════
// Optimized Diagnostic
// ═══════════════════════════════════════════════════════════════════════════

export function diagnoseVectorOptimized(
  vector: SymbolicVector,
  context: KernelContext
): KernelDiagnostics {
  const timer = performanceMonitor.startTimer();

  const metrics = computeSymbolicMetricsOptimized(vector, context);
  const qualityScore = aggregateQualityScore(metrics);
  const warnings: string[] = [];

  // Generate warnings for anomalous conditions
  if (metrics.SDR > 0.7) warnings.push("High symbolic drift detected");
  if (metrics.MSI < 0.2) warnings.push("Low memetic saturation");
  if (metrics.ARF < -0.5) warnings.push("Strong archetype dissonance");
  if (metrics.RFR > 0.8) warnings.push("High runic flux volatility");
  if (metrics.Hσ > 0.9) warnings.push("Excessive entropy");
  if (metrics.λN < 0.3) warnings.push("Narrative relevance decay");
  if (metrics.ITC < 0.4) warnings.push("Low temporal coherence");

  timer.end("diagnoseVector", false);

  return {
    vector,
    metrics,
    qualityScore,
    warnings,
    timestamp: Date.now(),
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Performance Analytics
// ═══════════════════════════════════════════════════════════════════════════

export function getKernelPerformanceStats() {
  return {
    metricsComputation: performanceMonitor.getStats("computeSymbolicMetrics"),
    batchComputation: performanceMonitor.getStats("computeMetricsBatch"),
    diagnostics: performanceMonitor.getStats("diagnoseVector"),
    cacheSize: metricCache.size(),
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Re-export original functions for compatibility
// ═══════════════════════════════════════════════════════════════════════════

export {
  computeSDR,
  computeMSI,
  computeARF,
  computeNMC,
  computeRFR,
  computeHσ,
  computeλN,
  computeITC,
  aggregateQualityScore,
};

export type { SymbolicVector, SymbolicMetrics, KernelContext, KernelDiagnostics };
