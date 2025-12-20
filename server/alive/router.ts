/**
 * ALIVE API Routes
 *
 * POST /alive/run - Run ALIVE analysis
 */

import type { Express } from "express";
import { aliveRunInputSchema, type AliveRunResult } from "@shared/alive/schema";
import { applyTierPolicy, validateTier, getUserTier } from "./policy";
import { isAuthenticated } from "../replitAuth";
import { spawn } from "child_process";

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

      // Apply tier policy (server-side filtering)
      const filtered = applyTierPolicy(result, userTier);

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
