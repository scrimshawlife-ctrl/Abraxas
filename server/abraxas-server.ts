/**
 * ABX-Core v1.2 - Abraxas Server Setup (Refactored)
 * SEED Framework Compliant
 *
 * @module abraxas-server
 * @entropy_class low
 * @deterministic false
 * @capabilities { read: ["all"], write: ["all"], network: true }
 *
 * Thin wrapper for Abraxas routing layer.
 * All business logic has been extracted to:
 * - server/abraxas/core/* (symbolic engines)
 * - server/abraxas/pipelines/* (oracle pipelines)
 * - server/abraxas/integrations/* (adapters)
 * - server/abraxas/routes/api.ts (clean routing)
 *
 * Previous code duplication eliminated:
 * - Rune system → server/runes.js
 * - Scoring logic → server/abraxas/pipelines/watchlist-scorer.ts
 * - Metrics → server/metrics.js
 * - Database → server/abraxas/integrations/sqlite-adapter.ts
 */

import type { Express } from "express";
import type { Server } from "http";

// Import clean routing layer (no duplication)
import { registerAbraxasRoutes } from "./abraxas/routes/api";

/**
 * Setup Abraxas routes on Express application
 * This is now a thin wrapper that delegates to the modular routing layer
 *
 * @param app - Express application
 * @param server - HTTP server instance
 */
export function setupAbraxasRoutes(app: Express, server: Server): void {
  // Delegate to modular routing layer
  registerAbraxasRoutes(app, server);

  console.log("🔮 Abraxas server setup complete (refactored architecture)");
}
