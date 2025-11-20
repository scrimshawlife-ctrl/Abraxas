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
import { getCacheStats, clearAllCaches, performanceMonitor } from "../core/performance";
import { getKernelPerformanceStats } from "../core/kernel-optimized";

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

  // ═══════════════════════════════════════════════════════════════════════════
  // ERS (Event-driven Ritual Scheduler) Management Endpoints
  // ═══════════════════════════════════════════════════════════════════════════

  // Import ERS scheduler
  const { scheduler } = require("../integrations/ers-scheduler");

  /**
   * GET /api/scheduler/status
   * Get scheduler status
   */
  app.get("/api/scheduler/status", (req, res) => {
    const status = scheduler.getStatus();
    res.json(status);
  });

  /**
   * GET /api/scheduler/tasks
   * Get all registered tasks
   */
  app.get("/api/scheduler/tasks", (req, res) => {
    const tasks = scheduler.getTasks().map((task: any) => ({
      id: task.id,
      name: task.name,
      description: task.description,
      pipeline: task.pipeline,
      trigger: task.trigger,
      enabled: task.enabled,
      deterministic: task.deterministic,
      entropy_class: task.entropy_class,
    }));
    res.json(tasks);
  });

  /**
   * GET /api/scheduler/tasks/:taskId
   * Get specific task details
   */
  app.get("/api/scheduler/tasks/:taskId", (req, res) => {
    const { taskId } = req.params;
    const task = scheduler.getTask(taskId);

    if (!task) {
      return res.status(404).json({ error: "Task not found" });
    }

    const schedule = scheduler.getSchedule(taskId);
    const recentExecutions = scheduler.getTaskExecutions(taskId, 5);

    res.json({
      task: {
        id: task.id,
        name: task.name,
        description: task.description,
        pipeline: task.pipeline,
        trigger: task.trigger,
        enabled: task.enabled,
        config: task.config,
      },
      schedule,
      recentExecutions,
    });
  });

  /**
   * POST /api/scheduler/tasks/:taskId/trigger
   * Manually trigger a task execution
   */
  app.post("/api/scheduler/tasks/:taskId/trigger", async (req, res) => {
    try {
      const { taskId } = req.params;
      const execution = await scheduler.triggerTask(taskId);
      res.json(execution);
    } catch (error) {
      console.error("Task trigger failed:", error);
      res.status(500).json({
        error: error instanceof Error ? error.message : "Failed to trigger task",
      });
    }
  });

  /**
   * POST /api/scheduler/tasks/:taskId/enable
   * Enable a task
   */
  app.post("/api/scheduler/tasks/:taskId/enable", (req, res) => {
    try {
      const { taskId } = req.params;
      scheduler.enableTask(taskId);
      res.json({ success: true, message: `Task ${taskId} enabled` });
    } catch (error) {
      res.status(500).json({
        error: error instanceof Error ? error.message : "Failed to enable task",
      });
    }
  });

  /**
   * POST /api/scheduler/tasks/:taskId/disable
   * Disable a task
   */
  app.post("/api/scheduler/tasks/:taskId/disable", (req, res) => {
    try {
      const { taskId } = req.params;
      scheduler.disableTask(taskId);
      res.json({ success: true, message: `Task ${taskId} disabled` });
    } catch (error) {
      res.status(500).json({
        error: error instanceof Error ? error.message : "Failed to disable task",
      });
    }
  });

  /**
   * GET /api/scheduler/executions
   * Get recent task executions
   */
  app.get("/api/scheduler/executions", (req, res) => {
    const limit = parseInt(req.query.limit as string) || 20;
    const executions = scheduler.getRecentExecutions(limit);
    res.json(executions);
  });

  /**
   * GET /api/scheduler/executions/:executionId
   * Get specific execution details
   */
  app.get("/api/scheduler/executions/:executionId", (req, res) => {
    const { executionId } = req.params;
    const execution = scheduler.getExecution(executionId);

    if (!execution) {
      return res.status(404).json({ error: "Execution not found" });
    }

    res.json(execution);
  });

  // ═══════════════════════════════════════════════════════════════════════════
  // Performance Monitoring Endpoints
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * GET /api/performance/stats
   * Get performance and cache statistics
   */
  app.get("/api/performance/stats", (req, res) => {
    const cacheStats = getCacheStats();
    const kernelStats = getKernelPerformanceStats();

    res.json({
      cache: {
        hashCacheSize: cacheStats.hashCacheSize,
        metricCacheSize: cacheStats.metricCacheSize,
      },
      kernel: kernelStats,
      performance: cacheStats.performanceMetrics,
      timestamp: Date.now(),
    });
  });

  /**
   * GET /api/performance/metrics
   * Get recent performance metrics
   */
  app.get("/api/performance/metrics", (req, res) => {
    const limit = parseInt(req.query.limit as string) || 100;
    const operation = req.query.operation as string;

    const metrics = performanceMonitor.getRecentMetrics(limit);
    const filtered = operation
      ? metrics.filter(m => m.operation === operation)
      : metrics;

    res.json({
      metrics: filtered,
      count: filtered.length,
      operations: performanceMonitor.getOperations(),
    });
  });

  /**
   * GET /api/performance/operations/:operation
   * Get detailed stats for a specific operation
   */
  app.get("/api/performance/operations/:operation", (req, res) => {
    const { operation } = req.params;
    const stats = performanceMonitor.getStats(operation);

    if (stats.count === 0) {
      return res.status(404).json({ error: "Operation not found" });
    }

    res.json({
      operation,
      stats,
      timestamp: Date.now(),
    });
  });

  /**
   * POST /api/performance/cache/clear
   * Clear all performance caches
   */
  app.post("/api/performance/cache/clear", (req, res) => {
    clearAllCaches();

    res.json({
      message: "All caches cleared successfully",
      timestamp: Date.now(),
    });
  });

  console.log("🔮 Abraxas API routes registered");
}
