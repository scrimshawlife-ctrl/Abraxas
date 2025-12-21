import type { Express } from "express";
import type { AliveRunResult } from "@shared/alive/schema";
import type { AliveWindow, AliveDigest } from "@shared/alive/digest";
import type { AliveBIRow } from "../exporter/export-bi-table";
import type { EmailSender } from "../../integrations/email/client";
import { isAuthenticated } from "../../replitAuth";
import { computeDigest } from "./compute";
import { formatDigestSlack, formatDigestEmail } from "./format";
import { postToSlackWebhook } from "../../integrations/slack/client";
import { getUserTier, validateTier } from "../policy";

const ALLOWED_WINDOWS: AliveWindow[] = ["7d", "30d", "90d"];

export function setupALIVEDigestRoutes(app: Express) {
  app.post("/api/alive/digest", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user?.claims?.sub || "unknown";
      const userTier = await getUserTier(userId);

      if (!validateTier(userTier)) {
        return res.status(400).json({
          success: false,
          error: "Invalid tier",
        });
      }

      if (userTier !== "enterprise") {
        return res.status(403).json({
          success: false,
          error: "Digest access requires enterprise tier",
        });
      }

      const {
        runs = [],
        biRows = [],
        window,
        scope,
        deliver,
        webhookUrl,
        recipients,
      } = req.body as {
        runs?: AliveRunResult[];
        biRows?: AliveBIRow[];
        window?: AliveWindow;
        scope?: AliveDigest["scope"];
        deliver?: "slack" | "email";
        webhookUrl?: string;
        recipients?: string[];
      };

      if (!window || !ALLOWED_WINDOWS.includes(window)) {
        return res.status(400).json({
          success: false,
          error: "Invalid or missing window",
        });
      }

      const digest = computeDigest({
        tier: userTier,
        window,
        scope,
        runs,
        biRows,
      });

      if (deliver === "slack") {
        if (!webhookUrl) {
          return res.status(400).json({
            success: false,
            error: "Missing Slack webhookUrl",
          });
        }
        const payload = formatDigestSlack(digest);
        await postToSlackWebhook(webhookUrl, payload);
        return res.json({ success: true, data: payload, digest });
      }

      if (deliver === "email") {
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
        const payload = formatDigestEmail(digest);
        await emailSender.send({
          to: recipients,
          subject: payload.subject,
          text: payload.text,
        });
        return res.json({ success: true, data: payload, digest });
      }

      return res.json({ success: true, data: digest });
    } catch (error: any) {
      console.error("Error generating ALIVE digest:", error);
      res.status(500).json({
        success: false,
        error: error.message || "Failed to generate digest",
      });
    }
  });
}
