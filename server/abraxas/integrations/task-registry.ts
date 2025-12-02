/**
 * ABX-Core v1.2 - Task Registry
 * SEED Framework Compliant
 *
 * @module abraxas/integrations/task-registry
 * @entropy_class low
 * @deterministic false (wraps pipelines)
 *
 * Registers all oracle pipelines as SymbolicTasks for ERS scheduling
 */

import type { SymbolicTask, TaskContext, TaskResult } from "../models/task";
import { generateDailyOracle, type OracleSnapshot } from "../pipelines/daily-oracle";
import { analyzeVCMarket, type VCAnalysisInput } from "../pipelines/vc-analyzer";
import { scanSocialTrends } from "../pipelines/social-scanner";
import { scoreWatchlists } from "../pipelines/watchlist-scorer";
import { generateWeatherOracle } from "../pipelines/weather-oracle";
// @ts-ignore - Legacy JS module
import metrics from "../../metrics";

/**
 * Daily Oracle Task
 * Generates daily ciphergram and oracle synthesis
 */
export const dailyOracleTask: SymbolicTask = {
  id: "daily-oracle",
  name: "Daily Oracle Generation",
  description: "Generate daily oracle ciphergram with symbolic analysis",
  pipeline: "daily-oracle",
  trigger: { type: "ritual", event: "daily" },
  enabled: true,
  deterministic: true,
  entropy_class: "medium",
  capabilities: {
    read: ["metrics"],
    write: [],
    network: false,
  },

  async executor(context: TaskContext): Promise<TaskResult> {
    const startTime = Date.now();

    try {
      // Get metrics snapshot
      const snapshot = metrics.snapshot();
      const oracleSnapshot: OracleSnapshot = {
        sources: snapshot.lifetime.sources.count || 0,
        signals: snapshot.lifetime.signals.count || 0,
        predictions: snapshot.lifetime.predictions.count || 0,
        accuracy: snapshot.lifetime.accuracy.acc || null,
      };

      // Generate oracle
      const oracle = generateDailyOracle(context.ritual, oracleSnapshot);

      const duration = Date.now() - startTime;

      return {
        success: true,
        data: oracle,
        metrics: {
          duration,
          quality: oracle.analysis.quality,
          drift: oracle.analysis.drift,
          entropy: oracle.analysis.entropy,
        },
        provenance: {
          taskId: context.taskId,
          executionId: context.executionId,
          seed: context.ritual.seed,
          timestamp: Date.now(),
        },
      };
    } catch (error) {
      const duration = Date.now() - startTime;
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        metrics: { duration },
        provenance: {
          taskId: context.taskId,
          executionId: context.executionId,
          seed: context.ritual.seed,
          timestamp: Date.now(),
        },
      };
    }
  },
};

/**
 * VC Analysis Task
 * Analyzes VC market trends for Technology/US by default
 */
export const vcAnalysisTask: SymbolicTask = {
  id: "vc-analysis",
  name: "VC Market Analysis",
  description: "Analyze venture capital market trends and forecasts",
  pipeline: "vc-analyzer",
  trigger: { type: "cron", expression: "0 0 * * *" }, // Daily at midnight
  enabled: false, // Disabled by default (manual trigger)
  deterministic: true,
  entropy_class: "medium",
  capabilities: {
    read: [],
    write: [],
    network: false,
  },
  config: {
    industry: "Technology",
    region: "US",
    horizonDays: 90,
  },

  async executor(context: TaskContext): Promise<TaskResult> {
    const startTime = Date.now();

    try {
      const input: VCAnalysisInput = {
        industry: context.trigger.type === "manual" && (context as any).input?.industry
          ? (context as any).input.industry
          : (this as SymbolicTask).config?.industry || "Technology",
        region: context.trigger.type === "manual" && (context as any).input?.region
          ? (context as any).input.region
          : (this as SymbolicTask).config?.region || "US",
        horizonDays: context.trigger.type === "manual" && (context as any).input?.horizonDays
          ? (context as any).input.horizonDays
          : (this as SymbolicTask).config?.horizonDays || 90,
      };

      const analysis = await analyzeVCMarket(input, context.ritual);

      const duration = Date.now() - startTime;

      return {
        success: true,
        data: analysis,
        metrics: {
          duration,
          quality: analysis.forecast.qualityScore,
          drift: analysis.symbolicAnalysis.drift,
          entropy: analysis.symbolicAnalysis.entropy,
        },
        provenance: {
          taskId: context.taskId,
          executionId: context.executionId,
          seed: context.ritual.seed,
          timestamp: Date.now(),
        },
      };
    } catch (error) {
      const duration = Date.now() - startTime;
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        metrics: { duration },
        provenance: {
          taskId: context.taskId,
          executionId: context.executionId,
          seed: context.ritual.seed,
          timestamp: Date.now(),
        },
      };
    }
  },
};

/**
 * Social Trends Scan Task
 * Scans social media platforms for trending keywords
 */
export const socialTrendsScanTask: SymbolicTask = {
  id: "social-trends-scan",
  name: "Social Trends Scanner",
  description: "Scan social media platforms for trending keywords",
  pipeline: "social-scanner",
  trigger: { type: "interval", milliseconds: 3600000 }, // Every hour
  enabled: false, // Disabled by default
  deterministic: true,
  entropy_class: "medium",
  capabilities: {
    read: [],
    write: [],
    network: false,
  },

  async executor(context: TaskContext): Promise<TaskResult> {
    const startTime = Date.now();

    try {
      const trends = scanSocialTrends(context.ritual);

      const duration = Date.now() - startTime;

      return {
        success: true,
        data: trends,
        metrics: {
          duration,
          quality: trends.meta.qualityScore,
          drift: trends.symbolicAnalysis.drift,
          entropy: trends.symbolicAnalysis.entropy,
        },
        provenance: {
          taskId: context.taskId,
          executionId: context.executionId,
          seed: context.ritual.seed,
          timestamp: Date.now(),
        },
      };
    } catch (error) {
      const duration = Date.now() - startTime;
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        metrics: { duration },
        provenance: {
          taskId: context.taskId,
          executionId: context.executionId,
          seed: context.ritual.seed,
          timestamp: Date.now(),
        },
      };
    }
  },
};

/**
 * Watchlist Scoring Task
 * Scores equity/FX watchlists
 */
export const watchlistScoringTask: SymbolicTask = {
  id: "watchlist-scoring",
  name: "Watchlist Scoring",
  description: "Score equity and FX watchlists with symbolic kernel",
  pipeline: "watchlist-scorer",
  trigger: { type: "ritual", event: "daily" },
  enabled: false, // Disabled by default (typically triggered by API)
  deterministic: true,
  entropy_class: "medium",
  capabilities: {
    read: ["watchlists"],
    write: [],
    network: false,
  },
  config: {
    equities: ["AAPL", "MSFT", "GOOGL"],
    fx: ["USD/JPY", "EUR/USD"],
  },

  async executor(context: TaskContext): Promise<TaskResult> {
    const startTime = Date.now();

    try {
      const watchlists = {
        equities: (this as SymbolicTask).config?.equities || [],
        fx: (this as SymbolicTask).config?.fx || [],
      };

      const results = await scoreWatchlists(watchlists, context.ritual);

      const duration = Date.now() - startTime;

      // Calculate average quality
      const allScores = [
        ...results.equities.conservative.map((e: any) => e.confidence),
        ...results.equities.risky.map((e: any) => e.confidence),
        ...results.fx.conservative.map((f: any) => f.confidence),
        ...results.fx.risky.map((f: any) => f.confidence),
      ];
      const avgQuality =
        allScores.length > 0
          ? allScores.reduce((sum, c) => sum + c, 0) / allScores.length
          : 0;

      return {
        success: true,
        data: results,
        metrics: {
          duration,
          quality: avgQuality,
        },
        provenance: {
          taskId: context.taskId,
          executionId: context.executionId,
          seed: context.ritual.seed,
          timestamp: Date.now(),
        },
      };
    } catch (error) {
      const duration = Date.now() - startTime;
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        metrics: { duration },
        provenance: {
          taskId: context.taskId,
          executionId: context.executionId,
          seed: context.ritual.seed,
          timestamp: Date.now(),
        },
      };
    }
  },
};

/**
 * Weather Oracle Task
 * Runs Oracle → Weather Engine pipeline
 */
export const weatherOracleTask: SymbolicTask = {
  id: "weather-oracle",
  name: "Weather Oracle",
  description: "Generate semiotic weather forecast from oracle output",
  pipeline: "weather-oracle",
  trigger: { type: "ritual", event: "daily" },
  enabled: true,
  deterministic: true,
  entropy_class: "high",
  capabilities: {
    read: ["oracle_output", "symbolic_metrics"],
    write: ["weather_forecast"],
    network: false,
  },

  async executor(context: TaskContext): Promise<TaskResult> {
    const startTime = Date.now();

    try {
      const result = await generateWeatherOracle(context.ritual);

      const duration = Date.now() - startTime;

      return {
        success: true,
        data: result,
        metrics: {
          duration,
          quality: result.weather.metadata.qualityScore,
          processingTime: result.weather.metadata.processingTime,
        },
        provenance: {
          taskId: context.taskId,
          executionId: context.executionId,
          seed: context.ritual.seed,
          timestamp: Date.now(),
        },
      };
    } catch (error) {
      const duration = Date.now() - startTime;
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        metrics: { duration },
        provenance: {
          taskId: context.taskId,
          executionId: context.executionId,
          seed: context.ritual.seed,
          timestamp: Date.now(),
        },
      };
    }
  },
};

/**
 * All registered tasks
 */
export const ALL_TASKS: SymbolicTask[] = [
  dailyOracleTask,
  vcAnalysisTask,
  socialTrendsScanTask,
  watchlistScoringTask,
  weatherOracleTask,
];

/**
 * Register all tasks with ERS scheduler
 */
export function registerAllTasks(scheduler: any): void {
  for (const task of ALL_TASKS) {
    scheduler.registerTask(task);
  }
  console.log(`[Task Registry] Registered ${ALL_TASKS.length} tasks`);
}
