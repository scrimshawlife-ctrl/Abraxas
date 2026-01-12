/**
 * ABX-Core v1.2 - Performance Benchmark Suite
 *
 * Measures and compares performance of optimized vs non-optimized kernel operations
 */

import { describe, it, expect, beforeEach } from "vitest";
import { computeSymbolicMetrics, type SymbolicVector, type KernelContext } from "../core/kernel";
import { computeSymbolicMetricsOptimized } from "../core/kernel-optimized";
import { clearAllCaches, performanceMonitor } from "../core/performance";
import { FIXED_RITUAL, FIXED_FEATURE_VECTOR } from "./fixtures";
import { ritualToContext } from "../integrations/runes-adapter";
import { generateDailyOracle } from "../pipelines/daily-oracle";

describe("Performance Benchmarks", () => {
  beforeEach(() => {
    // Clear caches before each test for fair comparison
    clearAllCaches();
  });

  it("should measure single metric computation performance", () => {
    const context = ritualToContext(FIXED_RITUAL);
    const vector: SymbolicVector = {
      features: FIXED_FEATURE_VECTOR,
      timestamp: Date.now(),
      seed: FIXED_RITUAL.seed,
    };

    // Warmup
    computeSymbolicMetrics(vector, context);
    computeSymbolicMetricsOptimized(vector, context);

    // Measure non-optimized
    const startOriginal = performance.now();
    for (let i = 0; i < 100; i++) {
      computeSymbolicMetrics(vector, context);
    }
    const durationOriginal = performance.now() - startOriginal;

    // Clear cache
    clearAllCaches();

    // Measure optimized (first run - no cache)
    const startOptimizedNoCacheWarmup = performance.now();
    computeSymbolicMetricsOptimized(vector, context);
    const durationOptimizedNoCacheWarmup = performance.now() - startOptimizedNoCacheWarmup;

    clearAllCaches();

    const startOptimizedNoCache = performance.now();
    for (let i = 0; i < 100; i++) {
      computeSymbolicMetricsOptimized(vector, context);
    }
    const durationOptimizedNoCache = performance.now() - startOptimizedNoCache;

    // Clear cache again
    clearAllCaches();

    // Measure optimized (with cache after first run)
    computeSymbolicMetricsOptimized(vector, context); // Prime cache
    const startOptimizedCached = performance.now();
    for (let i = 0; i < 100; i++) {
      computeSymbolicMetricsOptimized(vector, context);
    }
    const durationOptimizedCached = performance.now() - startOptimizedCached;

    console.log("\n📊 Single Vector Benchmark (100 iterations):");
    console.log(`  Original:              ${durationOriginal.toFixed(2)}ms`);
    console.log(`  Optimized (no cache):  ${durationOptimizedNoCache.toFixed(2)}ms`);
    console.log(`  Optimized (cached):    ${durationOptimizedCached.toFixed(2)}ms`);
    console.log(`  Speedup (no cache):    ${(durationOriginal / durationOptimizedNoCache).toFixed(2)}x`);
    console.log(`  Speedup (cached):      ${(durationOriginal / durationOptimizedCached).toFixed(2)}x`);

    // Cached version should be significantly faster
    expect(durationOptimizedCached).toBeLessThan(durationOriginal);
  });

  it("should measure batch computation performance", () => {
    const context = ritualToContext(FIXED_RITUAL);

    // Create multiple vectors
    const vectors: SymbolicVector[] = Array.from({ length: 10 }, (_, i) => ({
      features: {
        ...FIXED_FEATURE_VECTOR,
        variant: i * 0.1, // Add variation
      },
      timestamp: Date.now() + i,
      seed: FIXED_RITUAL.seed + i,
    }));

    // Warmup
    vectors.forEach(v => computeSymbolicMetrics(v, context));
    clearAllCaches();

    // Measure original (sequential)
    const startOriginal = performance.now();
    for (let run = 0; run < 10; run++) {
      vectors.forEach(v => computeSymbolicMetrics(v, context));
    }
    const durationOriginal = performance.now() - startOriginal;

    clearAllCaches();

    // Measure optimized (sequential)
    const startOptimized = performance.now();
    for (let run = 0; run < 10; run++) {
      vectors.forEach(v => computeSymbolicMetricsOptimized(v, context));
    }
    const durationOptimized = performance.now() - startOptimized;

    console.log("\n📊 Batch Processing Benchmark (10 vectors × 10 runs):");
    console.log(`  Original:   ${durationOriginal.toFixed(2)}ms`);
    console.log(`  Optimized:  ${durationOptimized.toFixed(2)}ms`);
    console.log(`  Speedup:    ${(durationOriginal / durationOptimized).toFixed(2)}x`);

    expect(durationOptimized).toBeLessThanOrEqual(durationOriginal * 1.25);
  });

  it("should measure cache hit rate effectiveness", () => {
    const context = ritualToContext(FIXED_RITUAL);
    const vector: SymbolicVector = {
      features: FIXED_FEATURE_VECTOR,
      timestamp: Date.now(),
      seed: FIXED_RITUAL.seed,
    };

    clearAllCaches();

    // Run 100 computations on same vector
    const iterations = 100;
    for (let i = 0; i < iterations; i++) {
      computeSymbolicMetricsOptimized(vector, context);
    }

    // Check performance monitor stats
    const stats = performanceMonitor.getStats("computeSymbolicMetrics");

    console.log("\n📊 Cache Hit Rate Analysis:");
    console.log(`  Total calls:       ${stats.count}`);
    console.log(`  Cache hit rate:    ${(stats.cacheHitRate * 100).toFixed(1)}%`);
    console.log(`  Avg duration:      ${stats.avgDuration.toFixed(3)}ms`);
    console.log(`  Min duration:      ${stats.minDuration.toFixed(3)}ms`);
    console.log(`  Max duration:      ${stats.maxDuration.toFixed(3)}ms`);

    // Cache hit rate should be high (>95% after first computation)
    expect(stats.cacheHitRate).toBeGreaterThan(0.95);
  });

  it("should measure memory efficiency", () => {
    const context = ritualToContext(FIXED_RITUAL);

    // Create many unique vectors
    const vectors: SymbolicVector[] = Array.from({ length: 1000 }, (_, i) => ({
      features: {
        value1: Math.random(),
        value2: Math.random(),
        value3: Math.random(),
      },
      timestamp: Date.now() + i,
      seed: FIXED_RITUAL.seed + i,
    }));

    clearAllCaches();

    const startMem = process.memoryUsage();

    // Compute metrics for all vectors
    vectors.forEach(v => computeSymbolicMetricsOptimized(v, context));

    const endMem = process.memoryUsage();
    const heapDelta = (endMem.heapUsed - startMem.heapUsed) / 1024 / 1024;

    console.log("\n📊 Memory Usage (1000 unique vectors):");
    console.log(`  Heap delta:    ${heapDelta.toFixed(2)} MB`);
    console.log(`  Per vector:    ${(heapDelta * 1024 / vectors.length).toFixed(2)} KB`);

    // Should not use excessive memory
    expect(heapDelta).toBeLessThan(50); // Less than 50MB for 1000 vectors
  });

  it("should measure hash cache effectiveness", () => {
    clearAllCaches();

    const context = ritualToContext(FIXED_RITUAL);
    const vector: SymbolicVector = {
      features: FIXED_FEATURE_VECTOR,
      timestamp: Date.now(),
      seed: FIXED_RITUAL.seed,
    };

    // Compute metrics multiple times
    const iterations = 50;
    const start = performance.now();
    for (let i = 0; i < iterations; i++) {
      computeSymbolicMetricsOptimized(vector, context);
    }
    const duration = performance.now() - start;

    const avgPerIteration = duration / iterations;

    console.log("\n📊 Hash Cache Performance:");
    console.log(`  Total duration:    ${duration.toFixed(2)}ms`);
    console.log(`  Avg per iteration: ${avgPerIteration.toFixed(3)}ms`);
    console.log(`  Iterations:        ${iterations}`);

    // Average should be very fast with caching
    expect(avgPerIteration).toBeLessThan(1); // Less than 1ms per iteration
  });

  it("should compare pipeline performance (daily oracle)", () => {
    const metricsSnapshot = {
      sources: 50,
      signals: 25,
      predictions: 10,
      accuracy: 0.75,
    };

    clearAllCaches();

    // Warmup
    generateDailyOracle(FIXED_RITUAL, metricsSnapshot);

    clearAllCaches();

    // Measure cold cache
    const startCold = performance.now();
    for (let i = 0; i < 10; i++) {
      clearAllCaches();
      generateDailyOracle(FIXED_RITUAL, metricsSnapshot);
    }
    const durationCold = performance.now() - startCold;

    clearAllCaches();

    // Measure warm cache
    generateDailyOracle(FIXED_RITUAL, metricsSnapshot); // Prime cache
    const startWarm = performance.now();
    for (let i = 0; i < 10; i++) {
      generateDailyOracle(FIXED_RITUAL, metricsSnapshot);
    }
    const durationWarm = performance.now() - startWarm;

    console.log("\n📊 Daily Oracle Pipeline (10 runs):");
    console.log(`  Cold cache:  ${durationCold.toFixed(2)}ms (${(durationCold/10).toFixed(2)}ms avg)`);
    console.log(`  Warm cache:  ${durationWarm.toFixed(2)}ms (${(durationWarm/10).toFixed(2)}ms avg)`);
    console.log(`  Speedup:     ${(durationCold / durationWarm).toFixed(2)}x`);

    expect(durationWarm).toBeLessThan(durationCold);
  });

  it("should verify determinism is preserved", () => {
    const context = ritualToContext(FIXED_RITUAL);
    const vector: SymbolicVector = {
      features: FIXED_FEATURE_VECTOR,
      timestamp: Date.now(),
      seed: FIXED_RITUAL.seed,
    };

    clearAllCaches();

    // Compute with original
    const original = computeSymbolicMetrics(vector, context);

    // Compute with optimized (no cache)
    clearAllCaches();
    const optimizedNoCache = computeSymbolicMetricsOptimized(vector, context);

    // Compute with optimized (cached)
    const optimizedCached = computeSymbolicMetricsOptimized(vector, context);

    console.log("\n📊 Determinism Verification:");
    console.log("  Original SDR:      ", original.SDR);
    console.log("  Optimized SDR:     ", optimizedNoCache.SDR);
    console.log("  Cached SDR:        ", optimizedCached.SDR);
    console.log("  Match:             ", original.SDR === optimizedNoCache.SDR && original.SDR === optimizedCached.SDR);

    // All versions should produce identical results
    expect(optimizedNoCache).toEqual(original);
    expect(optimizedCached).toEqual(original);
  });
});
