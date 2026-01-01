import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { setupAuth, isAuthenticated } from "./replitAuth";
import { setupAbraxasRoutes } from "./abraxas-server";
import { setupALIVERoutes } from "./alive/router";
import {
  insertUserSchema,
  insertTradingConfigSchema,
  insertRitualHistorySchema,
  insertPredictionSchema,
  insertMysticalMetricsSchema,
  insertUserSessionSchema,
  insertIndicatorSchema,
  insertWatchlistSchema,
  insertWatchlistItemSchema
} from "@shared/schema";
import { sql } from "drizzle-orm";
import { registerIndicator, discoverIndicators } from "./indicators";
import { analyzeSymbolPool, updateWatchlistAnalysis } from "./market-analysis";
import rateLimit from "express-rate-limit";
import { setupArtifactLensRoutes } from "./artifacts/routes";

// Extend global type for rate limiting
declare global {
  var rateLimitStore: Map<string, number[]>;
}

export async function registerRoutes(app: Express): Promise<Server> {
  // Create HTTP server
  const httpServer = createServer(app);

  // Read-only artifact dashboard endpoints (no auth, no writes)
  setupArtifactLensRoutes(app);

  // Rate limiting for authentication endpoints
  const authRateLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 5, // Limit each IP to 5 login requests per window
    message: { error: "Too many authentication attempts, please try again later" },
    standardHeaders: true,
    legacyHeaders: false,
  });

  // Setup authentication with rate limiting
  await setupAuth(app, authRateLimiter);

  // Setup Abraxas mystical trading routes
  setupAbraxasRoutes(app, httpServer);

  // Setup ALIVE routes
  setupALIVERoutes(app);

  // Auth endpoint
  app.get('/api/auth/user', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const user = await storage.getUser(userId);
      res.json(user);
    } catch (error) {
      console.error("Error fetching user:", error);
      res.status(500).json({ message: "Failed to fetch user" });
    }
  });

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

  app.get("/api/config", isAuthenticated, (req, res) => {
    res.json({ 
      weights: configStore, 
      defaults: configStore
    });
  });

  app.post("/api/config", isAuthenticated, (req, res) => {
    const { weights } = req.body || {};
    if (!weights || typeof weights !== "object") {
      return res.status(400).json({ error: "invalid_payload" });
    }
    // Update in-memory store
    configStore = { ...configStore, ...weights };
    res.json({ ok: true, weights: configStore });
  });

  // Config preview - test weights without persisting
  app.post("/api/config/preview", isAuthenticated, (req, res) => {
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

  // Indicator API routes
  app.get("/api/indicators", async (req, res) => {
    try {
      const indicators = await storage.getAllIndicators();
      res.json({ items: indicators });
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve indicators" });
    }
  });

  // Manual register (requires validation). Keep path obscure.
  app.post("/api/indicators/_register", async (req, res) => {
    try {
      // Rate limit check (simple in-memory implementation)
      const clientIP = req.ip || req.connection.remoteAddress || 'unknown';
      const rateLimitKey = `register_${clientIP}`;
      const now = Date.now();
      const RATE_LIMIT_WINDOW = 60 * 1000; // 1 minute
      const RATE_LIMIT_MAX = 5; // max 5 requests per minute
      
      if (!global.rateLimitStore) {
        global.rateLimitStore = new Map();
      }
      
      const requests = global.rateLimitStore.get(rateLimitKey) || [];
      const recentRequests = requests.filter((time: number) => now - time < RATE_LIMIT_WINDOW);
      
      if (recentRequests.length >= RATE_LIMIT_MAX) {
        return res.status(429).json({ error: "Rate limit exceeded. Try again later." });
      }
      
      recentRequests.push(now);
      global.rateLimitStore.set(rateLimitKey, recentRequests);

      // Validate request body with basic checks first
      const { name, slug } = req.body || {};
      if (!name || !slug) {
        return res.status(400).json({ error: "missing_name_or_slug" });
      }

      // Validate slug format separately before passing to registerIndicator
      const slugRegex = /^[a-z0-9-]{1,64}$/;
      if (!slugRegex.test(slug)) {
        return res.status(400).json({ 
          error: "invalid_slug", 
          details: "Slug must be alphanumeric with dashes, 1-64 characters" 
        });
      }

      // Validate name length
      if (name.length < 1 || name.length > 128) {
        return res.status(400).json({ 
          error: "invalid_name", 
          details: "Name must be 1-128 characters" 
        });
      }

      // Call registerIndicator to get proper SVG generation and config updates
      const rec = await registerIndicator({ name, slug });
      
      res.json({ ok: true, indicator: rec });
    } catch (error) {
      if (error instanceof Error && error.message.includes("unique constraint")) {
        res.status(409).json({ error: "Indicator with this key already exists" });
      } else {
        res.status(500).json({ error: "Failed to register indicator" });
      }
    }
  });

  // Trigger discovery now (restricted endpoint)
  app.post("/api/indicators/discover", async (req, res) => {
    try {
      // Rate limit check for discovery endpoint
      const clientIP = req.ip || req.connection.remoteAddress || 'unknown';
      const rateLimitKey = `discover_${clientIP}`;
      const now = Date.now();
      const RATE_LIMIT_WINDOW = 5 * 60 * 1000; // 5 minutes
      const RATE_LIMIT_MAX = 3; // max 3 requests per 5 minutes
      
      if (!global.rateLimitStore) {
        global.rateLimitStore = new Map();
      }
      
      const requests = global.rateLimitStore.get(rateLimitKey) || [];
      const recentRequests = requests.filter((time: number) => now - time < RATE_LIMIT_WINDOW);
      
      if (recentRequests.length >= RATE_LIMIT_MAX) {
        return res.status(429).json({ error: "Rate limit exceeded. Discovery is resource intensive." });
      }
      
      recentRequests.push(now);
      global.rateLimitStore.set(rateLimitKey, recentRequests);

      const minted = await discoverIndicators();
      res.json({ ok: true, minted });
    } catch (error) {
      res.status(500).json({ error: "Failed to discover indicators" });
    }
  });

  // ============================================================================
  // DYNAMIC WATCHLIST API ENDPOINTS
  // ============================================================================

  // Get all watchlists for authenticated user
  app.get("/api/watchlists", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const watchlists = await storage.getWatchlists(userId);
      res.json({ watchlists });
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch watchlists" });
    }
  });

  // Get specific watchlist with items (authenticated)
  app.get("/api/watchlists/:id", isAuthenticated, async (req: any, res) => {
    try {
      const { id } = req.params;
      const userId = req.user.claims.sub;
      const watchlist = await storage.getWatchlistById(id);
      
      if (!watchlist || watchlist.userId !== userId) {
        return res.status(404).json({ error: "Watchlist not found" });
      }
      
      const items = await storage.getWatchlistItems(id);
      res.json({ watchlist, items });
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch watchlist" });
    }
  });

  // Create new watchlist (authenticated)
  app.post("/api/watchlists", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const validation = insertWatchlistSchema.safeParse({
        ...req.body,
        userId
      });
      
      if (!validation.success) {
        return res.status(400).json({ 
          error: "validation_failed", 
          details: validation.error.errors 
        });
      }
      
      const watchlist = await storage.createWatchlist(validation.data);
      res.status(201).json({ watchlist });
    } catch (error) {
      res.status(500).json({ error: "Failed to create watchlist" });
    }
  });

  // Update watchlist
  app.put("/api/watchlists/:id", async (req, res) => {
    try {
      const { id } = req.params;
      const validation = insertWatchlistSchema.partial().safeParse(req.body);
      
      if (!validation.success) {
        return res.status(400).json({ 
          error: "validation_failed", 
          details: validation.error.errors 
        });
      }
      
      const watchlist = await storage.updateWatchlist(id, validation.data);
      
      if (!watchlist) {
        return res.status(404).json({ error: "Watchlist not found" });
      }
      
      res.json({ watchlist });
    } catch (error) {
      res.status(500).json({ error: "Failed to update watchlist" });
    }
  });

  // Delete watchlist
  app.delete("/api/watchlists/:id", async (req, res) => {
    try {
      const { id } = req.params;
      const success = await storage.deleteWatchlist(id);
      
      if (!success) {
        return res.status(404).json({ error: "Watchlist not found" });
      }
      
      res.json({ ok: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to delete watchlist" });
    }
  });

  // Get watchlist items (authenticated)
  app.get("/api/watchlists/:id/items", isAuthenticated, async (req: any, res) => {
    try {
      const { id } = req.params;
      const userId = req.user.claims.sub;
      
      // Verify the watchlist belongs to the authenticated user
      const watchlist = await storage.getWatchlistById(id);
      if (!watchlist || watchlist.userId !== userId) {
        return res.status(404).json({ error: "Watchlist not found" });
      }
      
      const items = await storage.getWatchlistItems(id);
      res.json(items);
    } catch (error) {
      console.error("Get watchlist items error:", error);
      res.status(500).json({ error: "Failed to get watchlist items" });
    }
  });

  // Add item to watchlist
  app.post("/api/watchlists/:id/items", async (req, res) => {
    try {
      const { id } = req.params;
      const validation = insertWatchlistItemSchema.safeParse({
        ...req.body,
        watchlistId: id
      });
      
      if (!validation.success) {
        return res.status(400).json({ 
          error: "validation_failed", 
          details: validation.error.errors 
        });
      }
      
      const item = await storage.addWatchlistItem(validation.data);
      res.status(201).json({ item });
    } catch (error) {
      res.status(500).json({ error: "Failed to add item to watchlist" });
    }
  });

  // Update watchlist item
  app.put("/api/watchlists/:watchlistId/items/:itemId", async (req, res) => {
    try {
      const { itemId } = req.params;
      const validation = insertWatchlistItemSchema.partial().safeParse(req.body);
      
      if (!validation.success) {
        return res.status(400).json({ 
          error: "validation_failed", 
          details: validation.error.errors 
        });
      }
      
      const item = await storage.updateWatchlistItem(itemId, validation.data);
      
      if (!item) {
        return res.status(404).json({ error: "Watchlist item not found" });
      }
      
      res.json({ item });
    } catch (error) {
      res.status(500).json({ error: "Failed to update watchlist item" });
    }
  });

  // Remove item from watchlist
  app.delete("/api/watchlists/:watchlistId/items/:itemId", async (req, res) => {
    try {
      const { itemId } = req.params;
      const success = await storage.removeWatchlistItem(itemId);
      
      if (!success) {
        return res.status(404).json({ error: "Watchlist item not found" });
      }
      
      res.json({ ok: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to remove item from watchlist" });
    }
  });

  // Analyze symbols and suggest candidates for watchlist
  app.post("/api/watchlists/analyze", async (req, res) => {
    try {
      const { symbols, analysisType, limit = 10 } = req.body;
      
      if (!symbols || !Array.isArray(symbols)) {
        return res.status(400).json({ error: "symbols array is required" });
      }
      
      if (!analysisType || !["growth", "short"].includes(analysisType)) {
        return res.status(400).json({ error: "analysisType must be 'growth' or 'short'" });
      }
      
      // Validate symbol format
      for (const item of symbols) {
        if (!item.symbol || !item.type || !["equity", "fx"].includes(item.type)) {
          return res.status(400).json({ 
            error: "Each symbol must have 'symbol' and 'type' ('equity' or 'fx')" 
          });
        }
      }
      
      const candidates = await analyzeSymbolPool(symbols, analysisType, limit);
      res.json({ candidates, analysisType });
    } catch (error) {
      res.status(500).json({ error: "Failed to analyze symbols" });
    }
  });

  // Refresh analysis for watchlist
  app.post("/api/watchlists/:id/refresh", async (req, res) => {
    try {
      const { id } = req.params;
      await updateWatchlistAnalysis(id);
      
      // Return updated watchlist with items
      const watchlist = await storage.getWatchlistById(id);
      const items = await storage.getWatchlistItems(id);
      
      res.json({ watchlist, items, refreshed: true });
    } catch (error) {
      if (error instanceof Error && error.message === "Watchlist not found") {
        return res.status(404).json({ error: "Watchlist not found" });
      }
      res.status(500).json({ error: "Failed to refresh watchlist analysis" });
    }
  });

  // Automatically generate growth/short watchlists (authenticated)
  app.post("/api/watchlists/auto-generate", isAuthenticated, async (req: any, res) => {
    console.log("Auto-generate endpoint called with body:", req.body);
    try {
      const userId = req.user.claims.sub; // Get user ID from authenticated session
      const { analysisType = "growth", symbolPool, limit = 10 } = req.body;
      
      
      if (!["growth", "short"].includes(analysisType)) {
        return res.status(400).json({ error: "analysisType must be 'growth' or 'short'" });
      }
      
      // Default symbol pool if not provided
      const defaultSymbolPool = [
        { symbol: "AAPL", type: "equity" }, { symbol: "MSFT", type: "equity" },
        { symbol: "GOOGL", type: "equity" }, { symbol: "TSLA", type: "equity" },
        { symbol: "NVDA", type: "equity" }, { symbol: "AMZN", type: "equity" },
        { symbol: "META", type: "equity" }, { symbol: "JPM", type: "equity" },
        { symbol: "EURUSD", type: "fx" }, { symbol: "GBPUSD", type: "fx" },
        { symbol: "USDJPY", type: "fx" }, { symbol: "AUDUSD", type: "fx" }
      ];
      
      const symbols = symbolPool || defaultSymbolPool;
      
      // Check if user already has a watchlist of this type
      let watchlist = await storage.getWatchlistByType(userId, analysisType);
      
      if (!watchlist) {
        // Create new watchlist
        watchlist = await storage.createWatchlist({
          userId,
          name: analysisType === "growth" ? "Growth Opportunities" : "Short Candidates",
          type: analysisType,
          description: `Automatically generated ${analysisType} watchlist based on market analysis`
        });
      }
      
      // Clear existing items
      const existingItems = await storage.getWatchlistItems(watchlist.id);
      for (const item of existingItems) {
        await storage.removeWatchlistItem(item.id);
      }
      
      // Analyze symbols and add top candidates
      console.log("About to call analyzeSymbolPool with:", { symbols: symbols.length, analysisType, limit });
      const candidates = await analyzeSymbolPool(symbols, analysisType, limit);
      console.log("AnalyzeSymbolPool returned:", candidates.length, "candidates");
      
      for (const candidate of candidates) {
        await storage.addWatchlistItem({
          watchlistId: watchlist.id,
          symbol: candidate.symbol,
          symbolType: candidate.symbolType,
          analysisScore: candidate.analysisScore,
          confidence: candidate.confidence,
          growthPotential: candidate.growthPotential,
          shortPotential: candidate.shortPotential,
          riskLevel: candidate.riskLevel,
          sector: candidate.sector,
          rationale: candidate.rationale,
          metadata: candidate.metadata
        });
      }
      
      // Update watchlist analysis timestamp
      await storage.updateWatchlist(watchlist.id, {
        lastAnalyzed: new Date()
      });
      
      const items = await storage.getWatchlistItems(watchlist.id);
      res.json({ watchlist, items, generated: true });
    } catch (error) {
      console.error("Auto-generate watchlist error:", error);
      res.status(500).json({ 
        error: "Failed to auto-generate watchlist",
        details: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  return httpServer;
}
