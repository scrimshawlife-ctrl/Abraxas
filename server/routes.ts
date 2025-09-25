import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { setupAbraxasRoutes } from "./abraxas-server";

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
      impact_summary: `Adjusted ${Object.keys(weights).length} weights. Primary influences: ${Object.entries(weights).slice(0,3).map(([k,v]) => `${k}(${v > 0 ? '+' : ''}${v.toFixed(2)})`).join(', ')}`
    };

    res.json({ 
      previewed: weights, 
      results: previewResults 
    });
  });

  // Example storage route (if needed)
  app.get("/api/example", (req, res) => {
    res.json({ message: "Abraxas mystical interface active", runes: "⟟Σ Active Σ⟟" });
  });

  return httpServer;
}
