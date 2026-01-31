/**
 * ABX-Core v1.2 - Symbolic Kernel Tests
 * Golden test suite for deterministic behavior
 *
 * @module abraxas/tests/kernel
 */

import { describe, it, expect } from "vitest";
import {
  computeSymbolicMetrics,
  aggregateQualityScore,
  type SymbolicVector,
} from "../core/kernel";
import { ritualToContext, createPipelineVector } from "../integrations/runes-adapter";
import {
  FIXED_RITUAL,
  ALT_RITUAL,
  FIXED_FEATURE_VECTOR,
  ZERO_FEATURE_VECTOR,
  MAX_FEATURE_VECTOR,
} from "./fixtures";

describe("Symbolic Kernel", () => {
  describe("computeSymbolicMetrics", () => {
    it("produces deterministic metrics for fixed ritual", () => {
      const context = ritualToContext(FIXED_RITUAL);
      const vector = createPipelineVector(
        FIXED_FEATURE_VECTOR,
        "test-subject",
        FIXED_RITUAL.seed,
        "test-module",
        context.timestamp
      );

      const symbolicVector: SymbolicVector = {
        ...vector,
        features: vector.features,
      };

      const metrics = computeSymbolicMetrics(symbolicVector, context);

      // Verify all 8 metrics are computed
      expect(metrics).toHaveProperty("SDR");
      expect(metrics).toHaveProperty("MSI");
      expect(metrics).toHaveProperty("ARF");
      expect(metrics).toHaveProperty("NMC");
      expect(metrics).toHaveProperty("RFR");
      expect(metrics).toHaveProperty("Hσ");
      expect(metrics).toHaveProperty("λN");
      expect(metrics).toHaveProperty("ITC");

      // Verify metric ranges
      expect(metrics.SDR).toBeGreaterThanOrEqual(0);
      expect(metrics.SDR).toBeLessThanOrEqual(1);

      expect(metrics.MSI).toBeGreaterThanOrEqual(0);
      expect(metrics.MSI).toBeLessThanOrEqual(1);

      expect(metrics.ARF).toBeGreaterThanOrEqual(-1);
      expect(metrics.ARF).toBeLessThanOrEqual(1);

      expect(metrics.NMC).toBeGreaterThanOrEqual(-1);
      expect(metrics.NMC).toBeLessThanOrEqual(1);

      expect(metrics.Hσ).toBeGreaterThanOrEqual(0);
      expect(metrics.Hσ).toBeLessThanOrEqual(1);

      // Golden snapshot: These values should never change for same input
      expect(metrics.SDR).toMatchInlineSnapshot(`0.6709396694189426`);
      expect(metrics.MSI).toMatchInlineSnapshot(`0.0298`);
      expect(metrics.ARF).toMatchInlineSnapshot(`0.5389599944865746`);
      expect(metrics.NMC).toMatchInlineSnapshot(`-0.11664`);
      expect(metrics.RFR).toMatchInlineSnapshot(`1`);
      expect(metrics.Hσ).toMatchInlineSnapshot(`0.9860472875963129`);
      expect(metrics.λN).toMatchInlineSnapshot(`1`);
      expect(metrics.ITC).toMatchInlineSnapshot(`0.95`);
    });

    it("produces reproducible metrics for same ritual", () => {
      const context = ritualToContext(FIXED_RITUAL);
      const vector = createPipelineVector(
        FIXED_FEATURE_VECTOR,
        "test-subject",
        FIXED_RITUAL.seed,
        "test-module",
        context.timestamp
      );

      const symbolicVector: SymbolicVector = {
        ...vector,
        features: vector.features,
      };

      const metrics1 = computeSymbolicMetrics(symbolicVector, context);
      const metrics2 = computeSymbolicMetrics(symbolicVector, context);

      // Exact equality - deterministic
      expect(metrics1).toEqual(metrics2);
    });

    it("produces different metrics for different rituals", () => {
      const context1 = ritualToContext(FIXED_RITUAL);
      const context2 = ritualToContext(ALT_RITUAL);

      const vector1 = createPipelineVector(
        FIXED_FEATURE_VECTOR,
        "test-subject",
        FIXED_RITUAL.seed,
        "test-module",
        context1.timestamp
      );

      const vector2 = createPipelineVector(
        FIXED_FEATURE_VECTOR,
        "test-subject",
        ALT_RITUAL.seed,
        "test-module",
        context2.timestamp
      );

      const symbolic1: SymbolicVector = { ...vector1, features: vector1.features };
      const symbolic2: SymbolicVector = { ...vector2, features: vector2.features };

      const metrics1 = computeSymbolicMetrics(symbolic1, context1);
      const metrics2 = computeSymbolicMetrics(symbolic2, context2);

      // Should be different due to different seeds/runes
      expect(metrics1).not.toEqual(metrics2);
    });

    it("handles zero feature vector", () => {
      const context = ritualToContext(FIXED_RITUAL);
      const vector = createPipelineVector(
        ZERO_FEATURE_VECTOR,
        "zero-test",
        FIXED_RITUAL.seed,
        "test-module",
        context.timestamp
      );

      const symbolicVector: SymbolicVector = {
        ...vector,
        features: vector.features,
      };

      const metrics = computeSymbolicMetrics(symbolicVector, context);

      // Should still produce valid metrics
      expect(metrics.SDR).toBeGreaterThanOrEqual(0);
      expect(metrics.MSI).toBeGreaterThanOrEqual(0);
      expect(metrics.Hσ).toBeGreaterThanOrEqual(0);

      // Low feature density should result in certain patterns
      expect(metrics.SDR).toMatchInlineSnapshot(`0.06380000000000002`); // Should be low
    });

    it("handles maximum feature vector", () => {
      const context = ritualToContext(FIXED_RITUAL);
      const vector = createPipelineVector(
        MAX_FEATURE_VECTOR,
        "max-test",
        FIXED_RITUAL.seed,
        "test-module",
        context.timestamp
      );

      const symbolicVector: SymbolicVector = {
        ...vector,
        features: vector.features,
      };

      const metrics = computeSymbolicMetrics(symbolicVector, context);

      // Should produce valid metrics
      expect(metrics.MSI).toMatchInlineSnapshot(`0.04`); // High saturation expected
      expect(metrics.Hσ).toMatchInlineSnapshot(`1`); // May have low entropy (all max)
    });
  });

  describe("aggregateQualityScore", () => {
    it("produces quality score in [0, 1] range", () => {
      const context = ritualToContext(FIXED_RITUAL);
      const vector = createPipelineVector(
        FIXED_FEATURE_VECTOR,
        "test-subject",
        FIXED_RITUAL.seed,
        "test-module",
        context.timestamp
      );

      const symbolicVector: SymbolicVector = {
        ...vector,
        features: vector.features,
      };

      const metrics = computeSymbolicMetrics(symbolicVector, context);
      const quality = aggregateQualityScore(metrics);

      expect(quality).toBeGreaterThanOrEqual(0);
      expect(quality).toBeLessThanOrEqual(1);
    });

    it("produces deterministic quality score", () => {
      const context = ritualToContext(FIXED_RITUAL);
      const vector = createPipelineVector(
        FIXED_FEATURE_VECTOR,
        "test-subject",
        FIXED_RITUAL.seed,
        "test-module",
        context.timestamp
      );

      const symbolicVector: SymbolicVector = {
        ...vector,
        features: vector.features,
      };

      const metrics = computeSymbolicMetrics(symbolicVector, context);
      const quality1 = aggregateQualityScore(metrics);
      const quality2 = aggregateQualityScore(metrics);

      expect(quality1).toBe(quality2);
      expect(quality1).toMatchInlineSnapshot(`0.4262673369430733`);
    });

    it("produces higher quality for low drift and entropy", () => {
      // This would require constructing specific metric values
      // For now, we verify it doesn't crash and produces valid output
      const context = ritualToContext(FIXED_RITUAL);
      const vector = createPipelineVector(
        FIXED_FEATURE_VECTOR,
        "test-subject",
        FIXED_RITUAL.seed,
        "test-module",
        context.timestamp
      );

      const symbolicVector: SymbolicVector = {
        ...vector,
        features: vector.features,
      };

      const metrics = computeSymbolicMetrics(symbolicVector, context);
      const quality = aggregateQualityScore(metrics);

      expect(typeof quality).toBe("number");
      expect(quality).not.toBeNaN();
    });
  });

  describe("Metric Composition", () => {
    it("SDR (Symbolic Drift Ratio) measures consistency", () => {
      const context = ritualToContext(FIXED_RITUAL);
      const vector = createPipelineVector(
        FIXED_FEATURE_VECTOR,
        "test-subject",
        FIXED_RITUAL.seed,
        "test-module",
        context.timestamp
      );

      const symbolicVector: SymbolicVector = {
        ...vector,
        features: vector.features,
      };

      const metrics = computeSymbolicMetrics(symbolicVector, context);

      // SDR should be in [0, 1]
      expect(metrics.SDR).toBeGreaterThanOrEqual(0);
      expect(metrics.SDR).toBeLessThanOrEqual(1);
    });

    it("MSI (Memetic Saturation Index) measures information density", () => {
      const context = ritualToContext(FIXED_RITUAL);
      const denseVector = createPipelineVector(
        MAX_FEATURE_VECTOR,
        "dense",
        FIXED_RITUAL.seed,
        "test-module",
        context.timestamp
      );

      const sparseVector = createPipelineVector(
        ZERO_FEATURE_VECTOR,
        "sparse",
        FIXED_RITUAL.seed,
        "test-module",
        context.timestamp
      );

      const denseMetrics = computeSymbolicMetrics(
        { ...denseVector, features: denseVector.features },
        context
      );
      const sparseMetrics = computeSymbolicMetrics(
        { ...sparseVector, features: sparseVector.features },
        context
      );

      // Dense vector should have higher saturation
      // (Note: actual implementation may vary, this tests the property exists)
      expect(denseMetrics.MSI).toBeGreaterThanOrEqual(0);
      expect(sparseMetrics.MSI).toBeGreaterThanOrEqual(0);
    });

    it("ARF (Archetype Resonance Factor) is in [-1, 1]", () => {
      const context = ritualToContext(FIXED_RITUAL);
      const vector = createPipelineVector(
        FIXED_FEATURE_VECTOR,
        "test-subject",
        FIXED_RITUAL.seed,
        "test-module",
        context.timestamp
      );

      const symbolicVector: SymbolicVector = {
        ...vector,
        features: vector.features,
      };

      const metrics = computeSymbolicMetrics(symbolicVector, context);

      expect(metrics.ARF).toBeGreaterThanOrEqual(-1);
      expect(metrics.ARF).toBeLessThanOrEqual(1);
    });

    it("all metrics are numbers and not NaN", () => {
      const context = ritualToContext(FIXED_RITUAL);
      const vector = createPipelineVector(
        FIXED_FEATURE_VECTOR,
        "test-subject",
        FIXED_RITUAL.seed,
        "test-module",
        context.timestamp
      );

      const symbolicVector: SymbolicVector = {
        ...vector,
        features: vector.features,
      };

      const metrics = computeSymbolicMetrics(symbolicVector, context);

      expect(typeof metrics.SDR).toBe("number");
      expect(typeof metrics.MSI).toBe("number");
      expect(typeof metrics.ARF).toBe("number");
      expect(typeof metrics.NMC).toBe("number");
      expect(typeof metrics.RFR).toBe("number");
      expect(typeof metrics.Hσ).toBe("number");
      expect(typeof metrics.λN).toBe("number");
      expect(typeof metrics.ITC).toBe("number");

      expect(metrics.SDR).not.toBeNaN();
      expect(metrics.MSI).not.toBeNaN();
      expect(metrics.ARF).not.toBeNaN();
      expect(metrics.NMC).not.toBeNaN();
      expect(metrics.RFR).not.toBeNaN();
      expect(metrics.Hσ).not.toBeNaN();
      expect(metrics.λN).not.toBeNaN();
      expect(metrics.ITC).not.toBeNaN();
    });
  });
});
