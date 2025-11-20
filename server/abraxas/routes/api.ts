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
// @ts-ignore - Legacy JS module
import metrics from "../../metrics";
// @ts-ignore - Legacy JS module
import { analyzeVC } from "../../vc_oracle";
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
   * Generates daily oracle ciphergram
   */
  app.get("/api/daily-oracle", (req, res) => {
    const s = metrics.snapshot();
    const conf = s.lifetime.accuracy.acc || 0.5;
    const tone = conf > 0.6 ? "ascending" : conf > 0.52 ? "tempered" : "probing";

    // Generate ciphergram
    const b = Buffer.from(
      JSON.stringify({ day: new Date().toISOString().slice(0, 10), tone })
    )
      .toString("base64")
      .replace(/=/g, "");

    const glyph = b.match(/.{1,8}/g)?.join("·") || b;

    res.json({
      ciphergram: `⟟Σ ${glyph} Σ⟟`,
      note: `Litany (${tone}): "Vectors converge; witnesses veiled."`,
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
   * Returns mock social media trends
   */
  app.get("/api/social-trends", (req, res) => {
    const trends = [
      {
        platform: "Twitter/X",
        trends: [
          { keyword: "AI", momentum: 0.85, sentiment: 0.72, volume: 125000 },
          {
            keyword: "blockchain",
            momentum: 0.43,
            sentiment: 0.58,
            volume: 89000,
          },
        ],
        timestamp: Date.now(),
      },
    ];
    res.json(trends);
  });

  /**
   * POST /api/social-trends/scan
   * Triggers social trends scan (mock implementation)
   */
  app.post("/api/social-trends/scan", async (req, res) => {
    const trends = [
      {
        platform: "Twitter/X",
        trends: [
          {
            keyword: "AI",
            momentum: Math.random(),
            sentiment: Math.random(),
            volume: Math.floor(Math.random() * 200000),
          },
          {
            keyword: "DeFi",
            momentum: Math.random(),
            sentiment: Math.random(),
            volume: Math.floor(Math.random() * 100000),
          },
        ],
        timestamp: Date.now(),
      },
    ];

    broadcast("social_trends", trends);
    res.json(trends);
  });

  // ═══════════════════════════════════════════════════════════════════════════
  // VC Oracle Endpoint
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * POST /api/vc/analyze
   * Venture capital analysis and forecasting
   */
  app.post("/api/vc/analyze", async (req, res) => {
    try {
      const {
        industry = "Technology",
        region = "US",
        horizonDays = 90,
      } = req.body || {};

      const analysis = await analyzeVC({ industry, region, horizonDays });

      res.json(analysis);
    } catch (error) {
      console.error("VC analysis failed:", error);
      res.status(500).json({ error: "Failed to analyze VC data" });
    }
  });

  console.log("🔮 Abraxas API routes registered");
}
