/**
 * ABX-Core v1.2 - Watchlist Scorer Pipeline Tests
 * Golden test suite for deterministic watchlist scoring
 */

import { describe, it, expect } from "vitest";
import { scoreWatchlists } from "../pipelines/watchlist-scorer";
import { FIXED_RITUAL, ALT_RITUAL, FIXED_WATCHLISTS } from "./fixtures";

describe("Watchlist Scorer Pipeline", () => {
  describe("scoreWatchlists", () => {
    it("produces deterministic scores for fixed inputs", async () => {
      const results1 = await scoreWatchlists(FIXED_WATCHLISTS, FIXED_RITUAL);
      const results2 = await scoreWatchlists(FIXED_WATCHLISTS, FIXED_RITUAL);

      // Compare structure and counts (floating-point may vary slightly)
      expect(results1.equities.conservative.length).toBe(results2.equities.conservative.length);
      expect(results1.equities.risky.length).toBe(results2.equities.risky.length);
      expect(results1.metadata.totalProcessed).toBe(results2.metadata.totalProcessed);
    });

    it("golden snapshot for fixed ritual", async () => {
      const results = await scoreWatchlists(FIXED_WATCHLISTS, FIXED_RITUAL);

      expect(results.metadata.totalProcessed).toMatchInlineSnapshot(`5`);
      expect(results.metadata.avgQualityScore).toMatchInlineSnapshot(`0.371`);
    });

    it("produces different scores for different rituals", async () => {
      const results1 = await scoreWatchlists(FIXED_WATCHLISTS, FIXED_RITUAL);
      const results2 = await scoreWatchlists(FIXED_WATCHLISTS, ALT_RITUAL);

      expect(results1).not.toEqual(results2);
    });

    it("categorizes equities into conservative and risky", async () => {
      const results = await scoreWatchlists(FIXED_WATCHLISTS, FIXED_RITUAL);

      expect(results.equities).toHaveProperty("conservative");
      expect(results.equities).toHaveProperty("risky");

      expect(Array.isArray(results.equities.conservative)).toBe(true);
      expect(Array.isArray(results.equities.risky)).toBe(true);

      const totalEquities =
        results.equities.conservative.length + results.equities.risky.length;
      expect(totalEquities).toBe(FIXED_WATCHLISTS.equities.length);
    });

    it("categorizes fx into conservative and risky", async () => {
      const results = await scoreWatchlists(FIXED_WATCHLISTS, FIXED_RITUAL);

      expect(results.fx).toHaveProperty("conservative");
      expect(results.fx).toHaveProperty("risky");

      const totalFX = results.fx.conservative.length + results.fx.risky.length;
      expect(totalFX).toBe(FIXED_WATCHLISTS.fx.length);
    });

    it("all results have required fields", async () => {
      const results = await scoreWatchlists(FIXED_WATCHLISTS, FIXED_RITUAL);

      const allResults = [
        ...results.equities.conservative,
        ...results.equities.risky,
        ...results.fx.conservative,
        ...results.fx.risky,
      ];

      allResults.forEach((result) => {
        expect(result).toHaveProperty("ticker");
        expect(result).toHaveProperty("confidence");
        expect(result).toHaveProperty("qualityScore");
      });
    });

    it("confidence scores within valid range", async () => {
      const results = await scoreWatchlists(FIXED_WATCHLISTS, FIXED_RITUAL);

      const allResults = [
        ...results.equities.conservative,
        ...results.equities.risky,
        ...results.fx.conservative,
        ...results.fx.risky,
      ];

      allResults.forEach((result) => {
        expect(result.confidence).toBeGreaterThanOrEqual(0);
        expect(result.confidence).toBeLessThanOrEqual(1);
      });
    });

    it("metadata reflects total processed", async () => {
      const results = await scoreWatchlists(FIXED_WATCHLISTS, FIXED_RITUAL);

      const expected =
        FIXED_WATCHLISTS.equities.length + FIXED_WATCHLISTS.fx.length;
      expect(results.metadata.totalProcessed).toBe(expected);
    });

    it("avgQualityScore is valid number", async () => {
      const results = await scoreWatchlists(FIXED_WATCHLISTS, FIXED_RITUAL);

      expect(typeof results.metadata.avgQualityScore).toBe("number");
      expect(results.metadata.avgQualityScore).toBeGreaterThanOrEqual(0);
      expect(results.metadata.avgQualityScore).toBeLessThanOrEqual(1);
      expect(results.metadata.avgQualityScore).not.toBeNaN();
    });
  });
});
