/**
 * ALIVE API Routes
 *
 * Endpoints for ALIVE analysis, export, and integrations.
 */

import type { Express } from "express";
import { aliveRunInputSchema } from "@shared/alive/schema";
import { exportRequestSchema } from "@shared/alive/exports";
import { runALIVEPipeline } from "./pipeline";
import { canExport, canIntegrate, validateTier, getUserTier } from "./policy";
import { createSignedExport, exportAsJSON } from "./export";
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
   * Export analysis in signed JSON format (golden artifact)
   */
  app.post("/api/alive/export", isAuthenticated, async (req: any, res) => {
    try {
      // Validate request
      const exportReq = exportRequestSchema.parse(req.body);

      // SECURITY: Get user tier from session/database (never trust client)
      // TODO: Implement getUserTier with actual DB lookup
      const userId = req.user?.claims?.sub || "unknown";
      const userTier = await getUserTier(userId);

      // Validate tier
      if (!validateTier(userTier)) {
        return res.status(400).json({
          success: false,
          error: "Invalid tier",
        });
      }

      // Check export permission
      if (!canExport(userTier, exportReq.format)) {
        return res.status(403).json({
          success: false,
          error: `Export format '${exportReq.format}' not allowed for tier '${userTier}'`,
        });
      }

      // TODO: Fetch field signature from database by analysisId
      // For now, return stub
      const fieldSignature: any = {
        analysisId: exportReq.analysisId,
        subjectId: "stub",
        timestamp: new Date().toISOString(),
        schemaVersion: "1.0.0",
        influence: [],
        vitality: [],
        lifeLogistics: [],
        compositeScore: {
          overall: 0.5,
          influenceWeight: 0.33,
          vitalityWeight: 0.34,
          lifeLogisticsWeight: 0.33,
        },
        corpusProvenance: [],
      };

      // Create signed export (golden artifact)
      const signedExport = createSignedExport(
        fieldSignature,
        userTier,
        exportReq.options
      );

      // Return as JSON (only format supported for now)
      if (exportReq.format === "json") {
        res.json({
          success: true,
          data: signedExport,
        });
      } else {
        // TODO: Implement CSV/PDF formats (derived from golden artifact)
        res.status(501).json({
          success: false,
          error: `Format '${exportReq.format}' not yet implemented`,
        });
      }
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
