/**
 * ALIVE API Routes
 *
 * Endpoints for ALIVE analysis, export, and integrations.
 */

import type { Express } from "express";
import { aliveRunInputSchema } from "@shared/alive/schema";
import { exportRequestSchema } from "@shared/alive/exports";
import { runALIVEPipeline } from "./pipeline";
import { canExport, canIntegrate } from "./policy";
import { isAuthenticated } from "../replitAuth";

export function setupALIVERoutes(app: Express) {
  /**
   * POST /api/alive/run
   * Run ALIVE analysis
   */
  app.post("/api/alive/run", isAuthenticated, async (req: any, res) => {
    try {
      // Validate input
      const input = aliveRunInputSchema.parse(req.body);

      // TODO: Get user tier from session/database
      // For now, use tier from request
      const userTier = input.tier;

      // Run pipeline
      const result = await runALIVEPipeline(input);

      // Return tier-filtered view
      res.json({
        success: true,
        data: result.filteredView,
        meta: {
          analysisId: result.fieldSignature.analysisId,
          tier: userTier,
          timestamp: result.fieldSignature.timestamp,
        },
      });
    } catch (error: any) {
      console.error("Error running ALIVE analysis:", error);
      res.status(500).json({
        success: false,
        error: error.message || "Failed to run ALIVE analysis",
      });
    }
  });

  /**
   * GET /api/alive/report/:analysisId
   * Retrieve existing analysis report
   */
  app.get("/api/alive/report/:analysisId", isAuthenticated, async (req, res) => {
    try {
      const { analysisId } = req.params;

      // TODO: Fetch from database
      // For now, return stub
      res.json({
        success: true,
        data: {
          analysisId,
          message: "Report retrieval not yet implemented",
        },
      });
    } catch (error: any) {
      console.error("Error fetching report:", error);
      res.status(500).json({
        success: false,
        error: error.message || "Failed to fetch report",
      });
    }
  });

  /**
   * POST /api/alive/export
   * Export analysis in specified format
   */
  app.post("/api/alive/export", isAuthenticated, async (req: any, res) => {
    try {
      // Validate request
      const exportReq = exportRequestSchema.parse(req.body);

      // TODO: Get user tier from session
      const userTier = exportReq.tier;

      // Check export permission
      if (!canExport(userTier, exportReq.format)) {
        return res.status(403).json({
          success: false,
          error: `Export format '${exportReq.format}' not allowed for tier '${userTier}'`,
        });
      }

      // TODO: Generate export file and return download URL
      res.json({
        success: true,
        data: {
          exportId: `export_${Date.now()}`,
          format: exportReq.format,
          downloadUrl: "/api/alive/downloads/stub",
          expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
          createdAt: new Date().toISOString(),
        },
      });
    } catch (error: any) {
      console.error("Error exporting ALIVE report:", error);
      res.status(500).json({
        success: false,
        error: error.message || "Failed to export report",
      });
    }
  });

  /**
   * POST /api/alive/integrations/slack
   * Configure Slack integration (enterprise only)
   */
  app.post(
    "/api/alive/integrations/slack",
    isAuthenticated,
    async (req: any, res) => {
      try {
        // TODO: Get user tier from session
        const userTier = req.body.tier || "psychonaut";

        // Check integration permission
        if (!canIntegrate(userTier, "slack")) {
          return res.status(403).json({
            success: false,
            error: "Slack integration not available for your tier",
          });
        }

        // TODO: Store Slack configuration
        res.json({
          success: true,
          message: "Slack integration configured",
        });
      } catch (error: any) {
        console.error("Error configuring Slack:", error);
        res.status(500).json({
          success: false,
          error: error.message || "Failed to configure Slack integration",
        });
      }
    }
  );
}
