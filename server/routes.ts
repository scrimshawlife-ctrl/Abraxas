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

  // Example storage route (if needed)
  app.get("/api/example", (req, res) => {
    res.json({ message: "Abraxas mystical interface active", runes: "⟟Σ Active Σ⟟" });
  });

  return httpServer;
}
