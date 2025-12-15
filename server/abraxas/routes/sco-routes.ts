/**
 * ABX-Core - SCO API Routes
 * Express routes for Symbolic Compression Operator
 * @module abraxas/routes/sco-routes
 */

import { Router, type Request, type Response } from "express";
import { analyzeSCO, scoToWeatherSignals } from "../pipelines/sco-analyzer";
import { computeSCOCompression, scoToWeatherNarrative } from "../weather_engine/modules/sco-compression";
import type { SCOLexiconEntry } from "../integrations/sco-bridge";

export const scoRouter = Router();

// ================================
// POST /sco/analyze
// ================================

interface AnalyzeRequest {
  texts: string[];
  domain?: string;
  customLexicon?: SCOLexiconEntry[];
}

scoRouter.post("/analyze", async (req: Request, res: Response) => {
  try {
    const { texts, domain, customLexicon }: AnalyzeRequest = req.body;

    if (!texts || !Array.isArray(texts)) {
      return res.status(400).json({ error: "texts array required" });
    }

    const result = await analyzeSCO({
      texts,
      domain,
      customLexicon,
    });

    res.json(result);
  } catch (error) {
    console.error("[SCO] Analysis error:", error);
    res.status(500).json({ error: "SCO analysis failed" });
  }
});

// ================================
// POST /sco/weather
// ================================

scoRouter.post("/weather", async (req: Request, res: Response) => {
  try {
    const { texts, domain, customLexicon }: AnalyzeRequest = req.body;

    if (!texts || !Array.isArray(texts)) {
      return res.status(400).json({ error: "texts array required" });
    }

    // Run SCO analysis
    const result = await analyzeSCO({
      texts,
      domain,
      customLexicon,
    });

    // Compute weather signal
    const weatherSignal = computeSCOCompression(result.events);

    // Generate narrative
    const narrative = scoToWeatherNarrative(weatherSignal);

    // Convert to weather engine signals
    const signals = scoToWeatherSignals(result);

    res.json({
      weatherSignal,
      narrative,
      signals,
      metadata: result.metadata,
    });
  } catch (error) {
    console.error("[SCO] Weather generation error:", error);
    res.status(500).json({ error: "SCO weather generation failed" });
  }
});

// ================================
// GET /sco/lexicons
// ================================

scoRouter.get("/lexicons", (_req: Request, res: Response) => {
  // Return available default lexicons
  const lexicons = {
    music: {
      description: "Music artist and genre compression patterns",
      entryCount: 3,
    },
    idiom: {
      description: "English idiom eggcorns and malapropisms",
      entryCount: 3,
    },
    crypto: {
      description: "Cryptocurrency terminology compression",
      entryCount: 2,
    },
    general: {
      description: "General-purpose compression detection",
      entryCount: 0,
    },
  };

  res.json({ lexicons });
});

// ================================
// Health check
// ================================

scoRouter.get("/health", (_req: Request, res: Response) => {
  res.json({
    status: "operational",
    module: "sco",
    version: "1.0.0",
    capabilities: ["analyze", "weather", "lexicons"],
  });
});

export function registerSCORoutes(app: any): void {
  app.use("/api/sco", scoRouter);
  console.log("[SCO] Routes registered at /api/sco/*");
}
