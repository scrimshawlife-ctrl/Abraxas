import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { setupAbraxasRoutes } from "./abraxas-server";
import { 
  insertUserSchema, 
  insertTradingConfigSchema,
  insertRitualHistorySchema,
  insertPredictionSchema,
  insertMysticalMetricsSchema,
  insertUserSessionSchema
} from "@shared/schema";
import { sql } from "drizzle-orm";

export async function registerRoutes(app: Express): Promise<Server> {
  // Create HTTP server
  const httpServer = createServer(app);

  // Setup Abraxas mystical trading routes
  setupAbraxasRoutes(app, httpServer);

  // Health endpoints
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", timestamp: Date.now(), service: "Abraxas Trading Oracle" });
  });

  // Config API (temporary in-memory storage)
  let configStore = {
    nightlights_z: 0.00,
    port_dwell_delta: 0.00,
    sam_mod_scope_delta: 0.00,
    ptab_ipr_burst: 0.00,
    fr_waiver_absence: 0.00,
    jobs_clearance_burst: 0.00,
    hs_code_volume_z: 0.00,
    fx_basis_z: 0.00,
    numerology_reduced: 0.00,
    numerology_master: 0.00,
    gematria_alignment: 0.00,
    astro_rul_align: 0.00,
    astro_waxing: 0.00
  };

  app.get("/api/config", (req, res) => {
    res.json({ 
      weights: configStore, 
      defaults: configStore
    });
  });

  app.post("/api/config", (req, res) => {
    const { weights } = req.body || {};
    if (!weights || typeof weights !== "object") {
      return res.status(400).json({ error: "invalid_payload" });
    }
    // Update in-memory store
    configStore = { ...configStore, ...weights };
    res.json({ ok: true, weights: configStore });
  });

  // Config preview - test weights without persisting
  app.post("/api/config/preview", (req, res) => {
    const { weights } = req.body || {};
    if (!weights || typeof weights !== "object") {
      return res.status(400).json({ error: "invalid_payload" });
    }
    
    // Create preview results with the proposed weights
    const previewResults = {
      equities: {
        conservative: [
          { ticker: "AAPL", score: 0.78 + (weights.nightlights_z || 0) * 0.1, confidence: "moderate" },
          { ticker: "MSFT", score: 0.82 + (weights.port_dwell_delta || 0) * 0.08, confidence: "high" }
        ],
        risky: [
          { ticker: "NVDA", score: 0.65 + (weights.gematria_alignment || 0) * 0.15, confidence: "volatile" },
          { ticker: "TSLA", score: 0.58 + (weights.astro_waxing || 0) * 0.12, confidence: "speculative" }
        ]
      },
      fx: {
        conservative: [
          { pair: "EURUSD", score: 0.71 + (weights.fx_basis_z || 0) * 0.09, confidence: "stable" }
        ],
        risky: [
          { pair: "USDJPY", score: 0.63 + (weights.numerology_reduced || 0) * 0.11, confidence: "dynamic" }
        ]
      },
      impact_summary: `Adjusted ${Object.keys(weights).length} weights. Primary influences: ${Object.entries(weights).slice(0,3).map(([k,v]) => `${k}(${typeof v === 'number' && v > 0 ? '+' : ''}${typeof v === 'number' ? v.toFixed(2) : v})`).join(', ')}`
    };

    res.json({ 
      previewed: weights, 
      results: previewResults 
    });
  });

  // User routes
  app.post("/api/users", async (req, res) => {
    try {
      const userData = insertUserSchema.parse(req.body);
      const user = await storage.createUser(userData);
      res.json(user);
    } catch (error) {
      res.status(400).json({ error: "Invalid user data" });
    }
  });

  app.get("/api/users/:username", async (req, res) => {
    try {
      const user = await storage.getUserByUsername(req.params.username);
      if (!user) {
        return res.status(404).json({ error: "User not found" });
      }
      res.json(user);
    } catch (error) {
      res.status(500).json({ error: "Internal server error" });
    }
  });

  // Trading Configuration routes
  app.get("/api/trading-configs", async (req, res) => {
    try {
      const { userId } = req.query;
      const configs = await storage.getTradingConfigs(userId as string);
      res.json(configs);
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve trading configs" });
    }
  });

  app.get("/api/trading-configs/:id", async (req, res) => {
    try {
      const config = await storage.getTradingConfig(req.params.id);
      if (!config) {
        return res.status(404).json({ error: "Trading config not found" });
      }
      res.json(config);
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve trading config" });
    }
  });

  app.post("/api/trading-configs", async (req, res) => {
    try {
      const configData = insertTradingConfigSchema.parse(req.body);
      const config = await storage.createTradingConfig(configData);
      res.json(config);
    } catch (error) {
      res.status(400).json({ error: "Invalid trading config data" });
    }
  });

  app.patch("/api/trading-configs/:id", async (req, res) => {
    try {
      const updateData = insertTradingConfigSchema.partial().parse(req.body);
      const config = await storage.updateTradingConfig(req.params.id, updateData);
      if (!config) {
        return res.status(404).json({ error: "Trading config not found" });
      }
      res.json(config);
    } catch (error) {
      res.status(400).json({ error: "Invalid trading config update data" });
    }
  });

  app.delete("/api/trading-configs/:id", async (req, res) => {
    try {
      const deleted = await storage.deleteTradingConfig(req.params.id);
      if (!deleted) {
        return res.status(404).json({ error: "Trading config not found" });
      }
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to delete trading config" });
    }
  });

  // Ritual History routes
  app.get("/api/ritual-history", async (req, res) => {
    try {
      const { userId, limit } = req.query;
      const rituals = await storage.getRitualHistory(
        userId as string, 
        limit ? parseInt(limit as string) : undefined
      );
      res.json(rituals);
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve ritual history" });
    }
  });

  app.post("/api/ritual-history", async (req, res) => {
    try {
      const ritualData = insertRitualHistorySchema.parse(req.body);
      const ritual = await storage.createRitualHistory(ritualData);
      res.json(ritual);
    } catch (error) {
      res.status(400).json({ error: "Invalid ritual history data" });
    }
  });

  app.patch("/api/ritual-history/:id/status", async (req, res) => {
    try {
      const { status, results } = req.body;
      const ritual = await storage.updateRitualStatus(req.params.id, status, results);
      if (!ritual) {
        return res.status(404).json({ error: "Ritual not found" });
      }
      res.json(ritual);
    } catch (error) {
      res.status(400).json({ error: "Failed to update ritual status" });
    }
  });

  // Predictions routes
  app.get("/api/predictions", async (req, res) => {
    try {
      const { userId, isResolved } = req.query;
      const predictions = await storage.getPredictions(
        userId as string,
        isResolved ? isResolved === 'true' : undefined
      );
      res.json(predictions);
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve predictions" });
    }
  });

  app.post("/api/predictions", async (req, res) => {
    try {
      const predictionData = insertPredictionSchema.parse(req.body);
      const prediction = await storage.createPrediction(predictionData);
      res.json(prediction);
    } catch (error) {
      res.status(400).json({ error: "Invalid prediction data" });
    }
  });

  app.patch("/api/predictions/:id/resolve", async (req, res) => {
    try {
      const { actualValue, accuracy } = req.body;
      const prediction = await storage.resolvePrediction(req.params.id, actualValue, accuracy);
      if (!prediction) {
        return res.status(404).json({ error: "Prediction not found" });
      }
      res.json(prediction);
    } catch (error) {
      res.status(400).json({ error: "Failed to resolve prediction" });
    }
  });

  // Mystical Metrics routes
  app.get("/api/mystical-metrics", async (req, res) => {
    try {
      const { userId, metricType, period } = req.query;
      const metrics = await storage.getMysticalMetrics(
        userId as string,
        metricType as string,
        period as string
      );
      res.json(metrics);
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve mystical metrics" });
    }
  });

  app.post("/api/mystical-metrics", async (req, res) => {
    try {
      const metricsData = insertMysticalMetricsSchema.parse(req.body);
      const metrics = await storage.createMysticalMetrics(metricsData);
      res.json(metrics);
    } catch (error) {
      res.status(400).json({ error: "Invalid mystical metrics data" });
    }
  });

  // User Sessions routes
  app.get("/api/user-sessions/:userId", async (req, res) => {
    try {
      const { limit } = req.query;
      const sessions = await storage.getUserSessions(
        req.params.userId,
        limit ? parseInt(limit as string) : undefined
      );
      res.json(sessions);
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve user sessions" });
    }
  });

  app.post("/api/user-sessions", async (req, res) => {
    try {
      const sessionData = insertUserSessionSchema.parse(req.body);
      const session = await storage.createUserSession(sessionData);
      res.json(session);
    } catch (error) {
      res.status(400).json({ error: "Invalid user session data" });
    }
  });

  app.patch("/api/user-sessions/:id/end", async (req, res) => {
    try {
      const { outcome, actions } = req.body;
      const session = await storage.endUserSession(req.params.id, outcome, actions);
      if (!session) {
        return res.status(404).json({ error: "User session not found" });
      }
      res.json(session);
    } catch (error) {
      res.status(400).json({ error: "Failed to end user session" });
    }
  });

  // Enhanced Abraxas status endpoint with database info
  app.get("/api/abraxas/status", (req, res) => {
    res.json({ 
      status: "active", 
      mystical_alignment: 0.873,
      database: "postgresql",
      tables_count: 6,
      runes: "⟟Σ Active Σ⟟"
    });
  });

  // Debug endpoint to verify database connection and table counts
  app.get("/api/debug/db-info", async (req, res) => {
    try {
      const { db } = require("./db");
      const { users, tradingConfigs, ritualHistory, predictions, mysticalMetrics, userSessions } = require("@shared/schema");
      
      // Get database info without exposing credentials
      const dbUrl = process.env.DATABASE_URL || "";
      const dbHost = dbUrl.includes("@") ? dbUrl.split("@")[1]?.split("/")[0] : "localhost";
      
      // Count records in each table
      const [
        userCount,
        configCount, 
        ritualCount,
        predictionCount,
        metricCount,
        sessionCount
      ] = await Promise.all([
        db.select({ count: sql`count(*)` }).from(users),
        db.select({ count: sql`count(*)` }).from(tradingConfigs),
        db.select({ count: sql`count(*)` }).from(ritualHistory),
        db.select({ count: sql`count(*)` }).from(predictions), 
        db.select({ count: sql`count(*)` }).from(mysticalMetrics),
        db.select({ count: sql`count(*)` }).from(userSessions)
      ]);

      res.json({
        database_host: dbHost,
        connection_status: "active",
        table_counts: {
          users: parseInt(userCount[0]?.count || "0"),
          trading_configs: parseInt(configCount[0]?.count || "0"),
          ritual_history: parseInt(ritualCount[0]?.count || "0"),
          predictions: parseInt(predictionCount[0]?.count || "0"),
          mystical_metrics: parseInt(metricCount[0]?.count || "0"),
          user_sessions: parseInt(sessionCount[0]?.count || "0")
        },
        timestamp: Date.now()
      });
    } catch (error) {
      console.error("Database debug error:", error);
      res.status(500).json({ 
        error: "Database connection failed", 
        details: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  return httpServer;
}
