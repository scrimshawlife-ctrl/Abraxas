/**
 * ABX-Core v1.2 - Social Scanner Pipeline Tests
 * Golden test suite for deterministic social trends analysis
 */

import { describe, it, expect } from "vitest";
import { scanSocialTrends } from "../pipelines/social-scanner";
import { FIXED_RITUAL, ALT_RITUAL } from "./fixtures";

describe("Social Scanner Pipeline", () => {
  describe("scanSocialTrends", () => {
    it("produces deterministic trends for fixed ritual", () => {
      const trends1 = scanSocialTrends(FIXED_RITUAL);
      const trends2 = scanSocialTrends(FIXED_RITUAL);

      // Compare structure (excluding timestamp which varies)
      expect(trends1.platforms.length).toBe(trends2.platforms.length);
      expect(trends1.meta.totalKeywords).toBe(trends2.meta.totalKeywords);
      expect(trends1.meta.avgMomentum).toBeCloseTo(trends2.meta.avgMomentum, 5);
      expect(trends1.meta.avgSentiment).toBeCloseTo(trends2.meta.avgSentiment, 5);
      expect(trends1.provenance.seed).toBe(trends2.provenance.seed);
    });

    it("golden snapshot for fixed ritual", () => {
      const trends = scanSocialTrends(FIXED_RITUAL);

      expect(trends.meta.totalKeywords).toMatchInlineSnapshot(`15`);
      expect(trends.meta.avgMomentum).toMatchInlineSnapshot(`0.4366666666666666`);
      expect(trends.meta.avgSentiment).toMatchInlineSnapshot(`0.5559999999999999`);
      expect(trends.symbolicAnalysis.memetic_saturation).toMatchInlineSnapshot(`0.04`);
    });

    it("produces different trends for different rituals", () => {
      const trends1 = scanSocialTrends(FIXED_RITUAL);
      const trends2 = scanSocialTrends(ALT_RITUAL);

      expect(trends1).not.toEqual(trends2);
      expect(trends1.provenance.seed).not.toBe(trends2.provenance.seed);
    });

    it("includes multiple platforms", () => {
      const trends = scanSocialTrends(FIXED_RITUAL);

      expect(Array.isArray(trends.platforms)).toBe(true);
      expect(trends.platforms.length).toBeGreaterThan(0);

      trends.platforms.forEach((platform) => {
        expect(platform).toHaveProperty("platform");
        expect(platform).toHaveProperty("trends");
        expect(platform).toHaveProperty("timestamp");
        expect(Array.isArray(platform.trends)).toBe(true);
      });
    });

    it("keyword trends have required fields", () => {
      const trends = scanSocialTrends(FIXED_RITUAL);

      const allTrends = trends.platforms.flatMap((p) => p.trends);
      expect(allTrends.length).toBeGreaterThan(0);

      allTrends.forEach((trend) => {
        expect(trend).toHaveProperty("keyword");
        expect(trend).toHaveProperty("momentum");
        expect(trend).toHaveProperty("sentiment");
        expect(trend).toHaveProperty("volume");
        expect(trend).toHaveProperty("saturation");
        expect(trend).toHaveProperty("archetype");
        expect(trend).toHaveProperty("confidence");
      });
    });

    it("metrics within valid ranges", () => {
      const trends = scanSocialTrends(FIXED_RITUAL);

      expect(trends.meta.avgMomentum).toBeGreaterThanOrEqual(0);
      expect(trends.meta.avgMomentum).toBeLessThanOrEqual(1);

      expect(trends.meta.avgSentiment).toBeGreaterThanOrEqual(0);
      expect(trends.meta.avgSentiment).toBeLessThanOrEqual(1);

      expect(trends.symbolicAnalysis.memetic_saturation).toBeGreaterThanOrEqual(0);
      expect(trends.symbolicAnalysis.memetic_saturation).toBeLessThanOrEqual(1);

      expect(trends.symbolicAnalysis.drift).toBeGreaterThanOrEqual(0);
      expect(trends.symbolicAnalysis.drift).toBeLessThanOrEqual(1);

      expect(trends.symbolicAnalysis.entropy).toBeGreaterThanOrEqual(0);
      expect(trends.symbolicAnalysis.entropy).toBeLessThanOrEqual(1);
    });

    it("includes provenance data", () => {
      const trends = scanSocialTrends(FIXED_RITUAL);

      expect(trends.provenance.seed).toBe(FIXED_RITUAL.seed);
      expect(trends.provenance.runes).toEqual(FIXED_RITUAL.runes.map((r) => r.id));
    });
  });
});
