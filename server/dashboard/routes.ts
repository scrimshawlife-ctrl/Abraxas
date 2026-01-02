import type { Express } from "express";

import { diffObjects } from "./diff";
import { ArtifactStore } from "./scan";

const store = new ArtifactStore();

export function registerDashboardRoutes(app: Express): void {
  // Keep behavior close to the proposed contract:
  // - rescan is explicit
  // - drift endpoints rescan on access (so reports appear without restart)

  app.get("/api/rescan", async (_req, res) => {
    await store.rescan();
    res.json({ ok: true });
  });

  app.get("/api/artifacts", async (_req, res) => {
    // cheap and safe to rescan (out/ may be updated out-of-band)
    await store.rescan();
    res.json(store.listArtifacts());
  });

  app.get("/api/artifacts/:artifactId/envelope", async (req, res) => {
    try {
      await store.rescan();
      res.json(store.getEnvelope(req.params.artifactId));
    } catch {
      res.status(404).json({ error: "Envelope not found" });
    }
  });

  app.get("/api/artifacts/:artifactId/narrative", async (req, res) => {
    try {
      await store.rescan();
      res.json(store.getNarrative(req.params.artifactId));
    } catch {
      res.status(404).json({ error: "Narrative not found" });
    }
  });

  app.get("/api/drift_reports", async (_req, res) => {
    await store.rescan();
    res.json(store.listDriftReports());
  });

  app.get("/api/drift_reports/:reportId", async (req, res) => {
    try {
      await store.rescan();
      res.json(store.getDrift(req.params.reportId));
    } catch {
      res.status(404).json({ error: "Drift report not found" });
    }
  });

  app.get("/api/diff", async (req, res) => {
    const left = String(req.query.left || "");
    const right = String(req.query.right || "");
    const kind = String(req.query.kind || "envelope");

    if (!left || !right) {
      return res.status(400).json({ error: "left and right are required" });
    }

    if (kind !== "envelope" && kind !== "narrative") {
      return res.status(400).json({ error: "Invalid kind" });
    }

    try {
      await store.rescan();
      const a = kind === "envelope" ? store.getEnvelope(left) : store.getNarrative(left);
      const b = kind === "envelope" ? store.getEnvelope(right) : store.getNarrative(right);
      res.json({ kind, left, right, changes: diffObjects(a, b) });
    } catch {
      res.status(404).json({ error: "Artifact not found" });
    }
  });
}

