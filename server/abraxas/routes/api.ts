/**
 * ABX-Core v1.2 - Abraxas API Routes
 * SEED Framework Compliant
 *
 * @module abraxas/routes/api
 * @entropy_class low
 * @deterministic false (handles HTTP requests)
 * @capabilities { read: ["all"], write: ["all"], network: true }
 *
 * Clean routing layer extracted from abraxas-server.ts
 * All business logic delegated to pipelines and core modules
 */

import type { Express } from "express";
import type { Server } from "http";
import crypto from "crypto";

// Import from existing modules (no duplication)
// @ts-ignore - Legacy JS modules, type declarations pending
import { getTodayRunes, runRitual } from "../../runes";
import { scoreWatchlists } from "../pipelines/watchlist-scorer";
import { generateDailyOracle, type OracleSnapshot } from "../pipelines/daily-oracle";
import { analyzeVCMarket } from "../pipelines/vc-analyzer";
import { getCurrentTrends, triggerTrendsScan } from "../pipelines/social-scanner";
// @ts-ignore - Legacy JS module
import metrics from "../../metrics";
import { sqliteDb } from "../integrations/sqlite-adapter";
import { initializeRitual } from "../integrations/runes-adapter";

/**
 * Register all Abraxas API routes
 */
export function registerAbraxasRoutes(app: Express, server: Server): void {
  // Broadcast functionality (disabled for now to avoid Vite WebSocket conflicts)
  const broadcast = (type: string, data: any) => {
    // console.log(`Broadcasting ${type}:`, data);
    // WebSocket functionality disabled to avoid conflicts with Vite
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // Health Endpoints
  // ═══════════════════════════════════════════════════════════════════════════

  app.get("/healthz", (req, res) => {
    res.json({ ok: true, ts: Date.now() });
  });

  app.get("/readyz", (req, res) => {
    try {
      const dbHealthy = sqliteDb.healthCheck();
      res.json({ ready: dbHealthy, ts: Date.now() });
    } catch (e) {
      res.status(503).json({ ready: false, error: String(e) });
    }
  });

  // ═══════════════════════════════════════════════════════════════════════════
  // Rune & Ritual Endpoints
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * GET /api/runes
   * Returns today's active runes
   */
  app.get("/api/runes", (req, res) => {
    const runes = getTodayRunes();
    res.json(runes);
  });

  /**
   * GET /api/stats
   * Returns metrics snapshot
   */
  app.get("/api/stats", (req, res) => {
    const snapshot = metrics.snapshot();
    res.json(snapshot);
  });

  /**
   * GET /api/daily-oracle
   * Generates daily oracle ciphergram with symbolic analysis
   */
  app.get("/api/daily-oracle", (req, res) => {
    const ritual = initializeRitual();
    const snapshot = metrics.snapshot();

    // Create oracle snapshot from metrics
    const oracleSnapshot: OracleSnapshot = {
      sources: snapshot.lifetime.sources.count || 0,
      signals: snapshot.lifetime.signals.count || 0,
      predictions: snapshot.lifetime.predictions.count || 0,
      accuracy: snapshot.lifetime.accuracy.acc || null,
    };

    // Generate oracle using pipeline
    const oracle = generateDailyOracle(ritual, oracleSnapshot);

    res.json({
      ciphergram: oracle.ciphergram,
      note: `Litany (${oracle.tone}): "${oracle.litany}"`,
      tone: oracle.tone,
      analysis: oracle.analysis,
      archetypes: oracle.archetypes,
      provenance: oracle.provenance,
    });
  });

  /**
   * POST /api/ritual
   * Execute ritual and score watchlists
   */
  app.post("/api/ritual", async (req, res) => {
    try {
      const { equities = [], fx = [] } = req.body || {};

      // Initialize ritual using ABX-Runes adapter
      const ritual = initializeRitual();

      // Score watchlists using refactored pipeline
      const results = await scoreWatchlists({ equities, fx }, ritual);

      // Add mock metrics (for demo purposes)
      ["federal_register", "sam.gov", "uspto"].forEach((s, i) =>
        metrics.addSource(
          crypto
            .createHash("md5")
            .update(s + i)
            .digest("hex")
            .substring(0, 12)
        )
      );

      ["rule:dfars", "mod:sam", "ipr:ptab"].forEach((s, i) =>
        metrics.addSignal(
          crypto
            .createHash("md5")
            .update(s + i)
            .digest("hex")
            .substring(0, 12)
        )
      );

      broadcast("results", { results });

      // Store ritual run in SQLite (legacy)
      try {
        sqliteDb.storeRitualRun({
          userId: "mock-user",
          date: ritual.date,
          seed: ritual.seed,
          runes: ritual.runes,
          results,
        });
      } catch (e) {
        console.log("DB insert failed (expected if no auth):", e);
      }

      // Generate seal
      const sealed = {
        hash: crypto
          .createHash("sha256")
          .update(JSON.stringify({ ritual, results }))
          .digest("hex")
          .substring(0, 16),
        timestamp: Date.now(),
        signature: `⟟Σ${crypto.randomBytes(4).toString("hex")}Σ⟟`,
      };

      res.json({
        ritual,
        results,
        sealed,
        disclaimer:
          "Abraxas persona is fictional; sources & methods sealed. Not financial advice.",
      });
    } catch (error) {
      console.error("Ritual execution failed:", error);
      res.status(500).json({ error: "Failed to execute ritual" });
    }
  });

  // ═══════════════════════════════════════════════════════════════════════════
  // Social Trends Endpoints
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * GET /api/social-trends
   * Returns current social media trends analysis
   */
  app.get("/api/social-trends", (req, res) => {
    const ritual = initializeRitual();
    const trends = getCurrentTrends(ritual);
    res.json(trends);
  });

  /**
   * POST /api/social-trends/scan
   * Triggers fresh social trends scan
   */
  app.post("/api/social-trends/scan", async (req, res) => {
    const ritual = initializeRitual();
    const trends = triggerTrendsScan(ritual);

    broadcast("social_trends", trends);
    res.json(trends);
  });

  // ═══════════════════════════════════════════════════════════════════════════
  // VC Oracle Endpoint
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * POST /api/vc/analyze
   * Venture capital analysis and forecasting with symbolic kernel
   */
  app.post("/api/vc/analyze", async (req, res) => {
    try {
      const {
        industry = "Technology",
        region = "US",
        horizonDays = 90,
      } = req.body || {};

      const ritual = initializeRitual();
      const analysis = await analyzeVCMarket(
        { industry, region, horizonDays },
        ritual
      );

      res.json(analysis);
    } catch (error) {
      console.error("VC analysis failed:", error);
      res.status(500).json({ error: "Failed to analyze VC data" });
    }
  });

  console.log("🔮 Abraxas API routes registered");
}
