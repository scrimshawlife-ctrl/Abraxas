/**
 * ABX-Core v1.2 - VC Analyzer Pipeline Tests
 * Golden test suite for deterministic VC market analysis
 */

import { describe, it, expect } from "vitest";
import { analyzeVCMarket } from "../pipelines/vc-analyzer";
import { FIXED_RITUAL, ALT_RITUAL, FIXED_VC_INPUT, ALT_VC_INPUT } from "./fixtures";

describe("VC Analyzer Pipeline", () => {
  describe("analyzeVCMarket", () => {
    it("produces deterministic analysis for fixed inputs", async () => {
      const analysis1 = await analyzeVCMarket(FIXED_VC_INPUT, FIXED_RITUAL);
      const analysis2 = await analyzeVCMarket(FIXED_VC_INPUT, FIXED_RITUAL);

      expect(analysis1).toEqual(analysis2);
    });

    it("golden snapshot for fixed ritual", async () => {
      const analysis = await analyzeVCMarket(FIXED_VC_INPUT, FIXED_RITUAL);

      expect(analysis.forecast.dealVolume.prediction).toMatchInlineSnapshot(`969`);
      expect(analysis.forecast.dealVolume.confidence).toMatchInlineSnapshot(`0.6`);
      expect(analysis.forecast.hotSectors.length).toMatchInlineSnapshot(`4`);
      expect(analysis.forecast.qualityScore).toMatchInlineSnapshot(`0.3525159527909272`);
    });

    it("produces different analysis for different inputs", async () => {
      const analysis1 = await analyzeVCMarket(FIXED_VC_INPUT, FIXED_RITUAL);
      const analysis2 = await analyzeVCMarket(ALT_VC_INPUT, FIXED_RITUAL);

      expect(analysis1.industry).not.toBe(analysis2.industry);
      expect(analysis1.forecast).not.toEqual(analysis2.forecast);
    });

    it("includes sector analysis with archetypes", async () => {
      const analysis = await analyzeVCMarket(FIXED_VC_INPUT, FIXED_RITUAL);

      expect(Array.isArray(analysis.forecast.hotSectors)).toBe(true);
      expect(analysis.forecast.hotSectors.length).toBeGreaterThan(0);

      analysis.forecast.hotSectors.forEach((sector) => {
        expect(sector).toHaveProperty("name");
        expect(sector).toHaveProperty("score");
        expect(sector).toHaveProperty("momentum");
        expect(sector).toHaveProperty("archetype");
        expect(sector).toHaveProperty("confidence");
      });
    });

    it("symbolic analysis within valid ranges", async () => {
      const analysis = await analyzeVCMarket(FIXED_VC_INPUT, FIXED_RITUAL);

      expect(analysis.symbolicAnalysis.drift).toBeGreaterThanOrEqual(0);
      expect(analysis.symbolicAnalysis.drift).toBeLessThanOrEqual(1);

      expect(analysis.symbolicAnalysis.saturation).toBeGreaterThanOrEqual(0);
      expect(analysis.symbolicAnalysis.saturation).toBeLessThanOrEqual(1);

      expect(analysis.symbolicAnalysis.resonance).toBeGreaterThanOrEqual(-1);
      expect(analysis.symbolicAnalysis.resonance).toBeLessThanOrEqual(1);

      expect(analysis.symbolicAnalysis.entropy).toBeGreaterThanOrEqual(0);
      expect(analysis.symbolicAnalysis.entropy).toBeLessThanOrEqual(1);
    });

    it("includes provenance data", async () => {
      const analysis = await analyzeVCMarket(FIXED_VC_INPUT, FIXED_RITUAL);

      expect(analysis.provenance.seed).toBe(FIXED_RITUAL.seed);
      expect(analysis.provenance.runes).toEqual(FIXED_RITUAL.runes.map((r) => r.id));
    });

    it("deal volume forecast is reasonable", async () => {
      const analysis = await analyzeVCMarket(FIXED_VC_INPUT, FIXED_RITUAL);

      expect(analysis.forecast.dealVolume.prediction).toBeGreaterThan(0);
      expect(analysis.forecast.dealVolume.confidence).toBeGreaterThanOrEqual(0.6);
      expect(analysis.forecast.dealVolume.confidence).toBeLessThanOrEqual(0.95);
    });

    it("sectors sorted by score descending", async () => {
      const analysis = await analyzeVCMarket(FIXED_VC_INPUT, FIXED_RITUAL);

      const scores = analysis.forecast.hotSectors.map((s) => s.score);
      const sorted = [...scores].sort((a, b) => b - a);

      expect(scores).toEqual(sorted);
    });
  });
});
