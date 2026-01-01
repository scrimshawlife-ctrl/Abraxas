/**
 * ALIVE API Routes
 *
 * POST /alive/run - Run ALIVE analysis
 */

import type { Express } from "express";
import { aliveRunInputSchema, type AliveRunResult } from "@shared/alive/schema";
import { applyTierPolicy, validateTier, getUserTier } from "./policy";
import { assertAllowed } from "./authorize";
import { exportAliveRun } from "./exporter";
import { computeEnterpriseAlerts } from "./alerts";
import { isAuthenticated } from "../replitAuth";
import { spawn } from "child_process";
import type { AliveExportFormat, AliveIntegration } from "@shared/alive/exports";
import { formatSlackMessage } from "../integrations/slack/format";
import { postToSlackWebhook } from "../integrations/slack/client";
import { formatAliveEmail } from "../integrations/email/format";
import type { EmailSender } from "../integrations/email/client";
import { postWebhook } from "../integrations/webhook/client";
import { setupALIVEDigestRoutes } from "./digest/route";

export function setupALIVERoutes(app: Express) {
  /**
   * POST /api/alive/run
   * Run ALIVE analysis on artifact
   */
  app.post("/api/alive/run", isAuthenticated, async (req: any, res) => {
    try {
      // Validate input
      const input = aliveRunInputSchema.parse(req.body);

      // SECURITY: Get user tier from session/database (never trust client)
      const userId = req.user?.claims?.sub || "unknown";
      const userTier = await getUserTier(userId);

      // Validate tier
      if (!validateTier(userTier)) {
        return res.status(400).json({
          success: false,
          error: "Invalid tier",
        });
      }

      // Call Python ALIVE core
      const result = await callPythonALIVE(input.artifact, userTier, input.profile);

      const enriched = {
        ...result,
        view: {
          ...result.view,
          alerts:
            userTier === "enterprise"
              ? computeEnterpriseAlerts(result)
              : result.view.alerts,
        },
      };

      // Apply tier policy (server-side filtering)
      const filtered = applyTierPolicy(enriched, userTier);

      // Return filtered view
      res.json({
        success: true,
        data: filtered,
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
   * POST /api/alive/export
   * Export ALIVE run result into a permitted format
   */
  app.post("/api/alive/export", isAuthenticated, async (req: any, res) => {
    try {
      const { run, format } = req.body as {
        run?: AliveRunResult;
        format?: AliveExportFormat;
      };

      if (!run || !format) {
        return res.status(400).json({
          success: false,
          error: "Missing run or format",
        });
      }

      const userId = req.user?.claims?.sub || "unknown";
      const userTier = await getUserTier(userId);

      if (!validateTier(userTier)) {
        return res.status(400).json({
          success: false,
          error: "Invalid tier",
        });
      }

      assertAllowed(userTier, format);

      const enriched = {
        ...run,
        view: {
          ...run.view,
          alerts:
            userTier === "enterprise"
              ? computeEnterpriseAlerts(run)
              : run.view?.alerts,
        },
      };
      const filtered = applyTierPolicy(enriched, userTier);
      const exported = exportAliveRun(filtered, format);

      res.json({ success: true, data: exported });
    } catch (error: any) {
      console.error("Error exporting ALIVE result:", error);
      res.status(500).json({
        success: false,
        error: error.message || "Failed to export ALIVE result",
      });
    }
  });

  /**
   * POST /api/alive/integrations/:integration
   * Deliver ALIVE payloads to integration channels (enterprise only)
   */
  app.post(
    "/api/alive/integrations/:integration",
    isAuthenticated,
    async (req: any, res) => {
      try {
        const integration = req.params.integration as AliveIntegration;
        const { run, webhookUrl, recipients } = req.body as {
          run?: AliveRunResult;
          webhookUrl?: string;
          recipients?: string[];
        };

        if (!run) {
          return res.status(400).json({
            success: false,
            error: "Missing run payload",
          });
        }

        const userId = req.user?.claims?.sub || "unknown";
        const userTier = await getUserTier(userId);

        if (!validateTier(userTier)) {
          return res.status(400).json({
            success: false,
            error: "Invalid tier",
          });
        }

        assertAllowed(userTier, undefined, integration);

        const enriched = {
          ...run,
          view: {
            ...run.view,
            alerts: computeEnterpriseAlerts(run),
          },
        };
        const filtered = applyTierPolicy(enriched, userTier);

        if (integration === "slack") {
          if (!webhookUrl) {
            return res.status(400).json({
              success: false,
              error: "Missing Slack webhookUrl",
            });
          }
          const payload = formatSlackMessage(filtered);
          await postToSlackWebhook(webhookUrl, payload);
          return res.json({ success: true, data: payload });
        }

        if (integration === "email") {
          const emailSender = (req.app?.locals?.emailSender as EmailSender) || null;
          if (!emailSender) {
            return res.status(500).json({
              success: false,
              error: "Email sender not configured",
            });
          }
          if (!recipients || recipients.length === 0) {
            return res.status(400).json({
              success: false,
              error: "Missing recipients",
            });
          }
          const payload = formatAliveEmail(filtered);
          await emailSender.send({
            to: recipients,
            subject: payload.subject,
            text: payload.text,
          });
          return res.json({ success: true, data: payload });
        }

        if (integration === "webhook") {
          if (!webhookUrl) {
            return res.status(400).json({
              success: false,
              error: "Missing webhookUrl",
            });
          }
          await postWebhook(webhookUrl, filtered);
          return res.json({ success: true });
        }

        return res.status(400).json({
          success: false,
          error: `Unsupported integration: ${integration}`,
        });
      } catch (error: any) {
        console.error("Error delivering integration payload:", error);
        res.status(500).json({
          success: false,
          error: error.message || "Failed integration delivery",
        });
      }
    }
  );

  setupALIVEDigestRoutes(app);
}

/**
 * Call Python ALIVE engine via subprocess.
 */
async function callPythonALIVE(
  artifact: any,
  tier: string,
  profile?: any
): Promise<AliveRunResult> {
  return new Promise((resolve, reject) => {
    const args = ["-m", "abraxas.alive.core", JSON.stringify(artifact), tier];
    
    const python = spawn("python3", args);
    
    let stdout = "";
    let stderr = "";

    python.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    python.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    python.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`Python process exited with code ${code}: ${stderr}`));
        return;
      }

      try {
        const result = JSON.parse(stdout);
        resolve(result as AliveRunResult);
      } catch (err) {
        reject(new Error(`Failed to parse Python output: ${err}`));
      }
    });

    python.on("error", (err) => {
      reject(new Error(`Failed to spawn Python process: ${err}`));
    });
  });
}
