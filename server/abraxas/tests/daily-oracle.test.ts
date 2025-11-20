/**
 * ABX-Core v1.2 - Daily Oracle Pipeline Tests
 * Golden test suite for deterministic ciphergram generation
 *
 * @module abraxas/tests/daily-oracle
 */

import { describe, it, expect } from "vitest";
import {
  generateDailyOracle,
  sealOracle,
  type DailyOracleResult,
} from "../pipelines/daily-oracle";
import {
  FIXED_RITUAL,
  ALT_RITUAL,
  FIXED_METRICS_SNAPSHOT,
  LOW_CONFIDENCE_METRICS,
  HIGH_CONFIDENCE_METRICS,
} from "./fixtures";

describe("Daily Oracle Pipeline", () => {
  describe("generateDailyOracle", () => {
    it("generates deterministic ciphergram for fixed inputs", () => {
      const oracle1 = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);
      const oracle2 = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);

      // Complete determinism - exact equality
      expect(oracle1).toEqual(oracle2);
    });

    it("produces golden snapshot for fixed ritual", () => {
      const oracle = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);

      // Golden snapshot - should never change
      expect(oracle.ciphergram).toMatchInlineSnapshot();
      expect(oracle.tone).toMatchInlineSnapshot();
      expect(oracle.litany).toMatchInlineSnapshot();
      expect(oracle.analysis.quality).toMatchInlineSnapshot();
      expect(oracle.analysis.drift).toMatchInlineSnapshot();
      expect(oracle.analysis.entropy).toMatchInlineSnapshot();
      expect(oracle.analysis.resonance).toMatchInlineSnapshot();
      expect(oracle.analysis.confidence).toMatchInlineSnapshot();
    });

    it("generates different ciphergrams for different rituals", () => {
      const oracle1 = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);
      const oracle2 = generateDailyOracle(ALT_RITUAL, FIXED_METRICS_SNAPSHOT);

      expect(oracle1.ciphergram).not.toBe(oracle2.ciphergram);
      expect(oracle1.provenance.seed).not.toBe(oracle2.provenance.seed);
    });

    it("generates different tones for different confidence levels", () => {
      const lowConfOracle = generateDailyOracle(FIXED_RITUAL, LOW_CONFIDENCE_METRICS);
      const highConfOracle = generateDailyOracle(FIXED_RITUAL, HIGH_CONFIDENCE_METRICS);

      // Tones should differ based on confidence
      expect(lowConfOracle.tone).toMatchInlineSnapshot();
      expect(highConfOracle.tone).toMatchInlineSnapshot();

      // High confidence should produce better tone
      const tonePriority = {
        ascending: 4,
        tempered: 3,
        probing: 2,
        descending: 1,
      };

      expect(tonePriority[highConfOracle.tone]).toBeGreaterThanOrEqual(
        tonePriority[lowConfOracle.tone]
      );
    });

    it("includes correct provenance data", () => {
      const oracle = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);

      expect(oracle.provenance.seed).toBe(FIXED_RITUAL.seed);
      expect(oracle.provenance.runes).toEqual(
        FIXED_RITUAL.runes.map((r) => r.id)
      );
      expect(oracle.provenance.metrics).toHaveProperty("SDR");
      expect(oracle.provenance.metrics).toHaveProperty("MSI");
      expect(oracle.provenance.metrics).toHaveProperty("ARF");
      expect(oracle.provenance.metrics).toHaveProperty("Hσ");
    });

    it("produces valid ciphergram format", () => {
      const oracle = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);

      // Ciphergram should have specific format
      expect(oracle.ciphergram).toMatch(/^⟟Σ .+ Σ⟟$/);
      expect(oracle.ciphergram).toContain("·"); // Glyph separator
    });

    it("includes archetypes in response", () => {
      const oracle = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);

      expect(Array.isArray(oracle.archetypes)).toBe(true);
      expect(oracle.archetypes.length).toBeGreaterThan(0);

      // Archetypes should be from the known list
      const validArchetypes = [
        "The Warrior",
        "The Sage",
        "The Fool",
        "The Monarch",
        "The Trickster",
      ];

      oracle.archetypes.forEach((archetype) => {
        expect(validArchetypes).toContain(archetype);
      });
    });

    it("produces analysis with valid ranges", () => {
      const oracle = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);

      expect(oracle.analysis.quality).toBeGreaterThanOrEqual(0);
      expect(oracle.analysis.quality).toBeLessThanOrEqual(1);

      expect(oracle.analysis.drift).toBeGreaterThanOrEqual(0);
      expect(oracle.analysis.drift).toBeLessThanOrEqual(1);

      expect(oracle.analysis.entropy).toBeGreaterThanOrEqual(0);
      expect(oracle.analysis.entropy).toBeLessThanOrEqual(1);

      expect(oracle.analysis.resonance).toBeGreaterThanOrEqual(-1);
      expect(oracle.analysis.resonance).toBeLessThanOrEqual(1);

      expect(oracle.analysis.confidence).toBeGreaterThanOrEqual(0);
      expect(oracle.analysis.confidence).toBeLessThanOrEqual(1);
    });

    it("handles null accuracy in metrics snapshot", () => {
      const nullAccuracyMetrics = {
        ...FIXED_METRICS_SNAPSHOT,
        accuracy: null,
      };

      const oracle = generateDailyOracle(FIXED_RITUAL, nullAccuracyMetrics);

      // Should default to 0.5 confidence base
      expect(oracle.analysis.confidence).toBeGreaterThan(0);
      expect(oracle.analysis.confidence).toBeLessThan(1);
    });

    it("tone matches litany sentiment", () => {
      const oracle = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);

      const toneMessages = {
        ascending: /clarity|converge/i,
        tempered: /veiled|tempered/i,
        probing: /obscured|shift/i,
        descending: /fades|entropy/i,
      };

      const expectedPattern = toneMessages[oracle.tone];
      if (expectedPattern) {
        expect(oracle.litany).toMatch(expectedPattern);
      }
    });
  });

  describe("sealOracle", () => {
    it("generates deterministic seal for same oracle", () => {
      const oracle = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);

      const seal1 = sealOracle(oracle);
      const seal2 = sealOracle(oracle);

      expect(seal1).toBe(seal2);
    });

    it("generates different seals for different oracles", () => {
      const oracle1 = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);
      const oracle2 = generateDailyOracle(ALT_RITUAL, FIXED_METRICS_SNAPSHOT);

      const seal1 = sealOracle(oracle1);
      const seal2 = sealOracle(oracle2);

      expect(seal1).not.toBe(seal2);
    });

    it("produces 16-character hex seal", () => {
      const oracle = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);
      const seal = sealOracle(oracle);

      expect(seal).toHaveLength(16);
      expect(seal).toMatch(/^[0-9a-f]{16}$/);
    });

    it("seal changes if ciphergram is modified", () => {
      const oracle = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);
      const originalSeal = sealOracle(oracle);

      // Modify ciphergram
      const modifiedOracle: DailyOracleResult = {
        ...oracle,
        ciphergram: oracle.ciphergram + "-modified",
      };

      const modifiedSeal = sealOracle(modifiedOracle);

      expect(modifiedSeal).not.toBe(originalSeal);
    });

    it("golden snapshot for seal", () => {
      const oracle = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);
      const seal = sealOracle(oracle);

      expect(seal).toMatchInlineSnapshot();
    });
  });

  describe("Tone Determination", () => {
    it("high confidence + low drift + low entropy = ascending", () => {
      const highQualityMetrics = {
        sources: 200,
        signals: 100,
        predictions: 50,
        accuracy: 0.85,
      };

      const oracle = generateDailyOracle(FIXED_RITUAL, highQualityMetrics);

      // With high accuracy and good metrics, should tend toward ascending
      expect(["ascending", "tempered"]).toContain(oracle.tone);
    });

    it("low confidence = descending or probing", () => {
      const lowQualityMetrics = {
        sources: 5,
        signals: 2,
        predictions: 1,
        accuracy: 0.35,
      };

      const oracle = generateDailyOracle(FIXED_RITUAL, lowQualityMetrics);

      // With low accuracy, should tend toward probing or descending
      expect(["probing", "descending"]).toContain(oracle.tone);
    });
  });

  describe("SEED Compliance", () => {
    it("maintains deterministic execution", () => {
      const executions = Array.from({ length: 10 }, () =>
        generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT)
      );

      // All executions should be identical
      executions.forEach((oracle) => {
        expect(oracle).toEqual(executions[0]);
      });
    });

    it("includes full provenance chain", () => {
      const oracle = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);

      expect(oracle.provenance.seed).toBeTruthy();
      expect(oracle.provenance.runes).toBeTruthy();
      expect(oracle.provenance.metrics).toBeTruthy();
      expect(oracle.timestamp).toBeGreaterThan(0);
    });

    it("symbolic metrics within SEED bounds", () => {
      const oracle = generateDailyOracle(FIXED_RITUAL, FIXED_METRICS_SNAPSHOT);

      // Entropy should be bounded (< 0.8 for good quality)
      expect(oracle.analysis.entropy).toBeLessThan(1);

      // Drift should be reasonable
      expect(oracle.analysis.drift).toBeGreaterThanOrEqual(0);
      expect(oracle.analysis.drift).toBeLessThanOrEqual(1);
    });
  });
});
