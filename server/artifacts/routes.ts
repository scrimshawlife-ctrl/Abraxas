import type { Express } from "express";
import {
  buildArtifactIndex,
  getArtifactRootDir,
  listDriftReports,
  readArtifactJsonByKind,
  validateArtifactId,
} from "./lens";

export function setupArtifactLensRoutes(app: Express) {
  // Read-only artifact lens. No auth required; no writes.
  app.get("/api/artifacts", async (_req, res) => {
    try {
      const rootDir = getArtifactRootDir();
      const index = await buildArtifactIndex(rootDir);
      res.json(index);
    } catch (error) {
      res.status(500).json({
        error: "artifact_index_failed",
        message: error instanceof Error ? error.message : "Unknown error",
      });
    }
  });

  app.get("/api/artifacts/:id/envelope", async (req, res) => {
    const id = req.params.id;
    if (!validateArtifactId(id)) {
      return res.status(400).json({ error: "invalid_artifact_id" });
    }
    try {
      const rootDir = getArtifactRootDir();
      const found = await readArtifactJsonByKind({
        rootDir,
        artifactId: id,
        kind: "oracle_envelope_v2",
      });
      if (!found) return res.status(404).json({ error: "artifact_envelope_not_found" });
      res.json(found.json);
    } catch (error) {
      res.status(500).json({
        error: "artifact_envelope_failed",
        message: error instanceof Error ? error.message : "Unknown error",
      });
    }
  });

  app.get("/api/artifacts/:id/narrative", async (req, res) => {
    const id = req.params.id;
    if (!validateArtifactId(id)) {
      return res.status(400).json({ error: "invalid_artifact_id" });
    }
    try {
      const rootDir = getArtifactRootDir();
      const found = await readArtifactJsonByKind({
        rootDir,
        artifactId: id,
        kind: "narrative_bundle_v1",
      });
      if (!found) return res.status(404).json({ error: "artifact_narrative_not_found" });
      res.json(found.json);
    } catch (error) {
      res.status(500).json({
        error: "artifact_narrative_failed",
        message: error instanceof Error ? error.message : "Unknown error",
      });
    }
  });

  app.get("/api/drift_reports", async (_req, res) => {
    try {
      const rootDir = getArtifactRootDir();
      const drift = await listDriftReports(rootDir);
      res.json({ root_dir: rootDir, items: drift });
    } catch (error) {
      res.status(500).json({
        error: "drift_report_index_failed",
        message: error instanceof Error ? error.message : "Unknown error",
      });
    }
  });

  app.get("/api/drift_reports/:id", async (req, res) => {
    const id = req.params.id;
    if (!validateArtifactId(id)) {
      return res.status(400).json({ error: "invalid_artifact_id" });
    }
    try {
      const rootDir = getArtifactRootDir();
      const found = await readArtifactJsonByKind({
        rootDir,
        artifactId: id,
        kind: "drift_report_v1",
      });
      if (!found) return res.status(404).json({ error: "drift_report_not_found" });
      res.json(found.json);
    } catch (error) {
      res.status(500).json({
        error: "drift_report_failed",
        message: error instanceof Error ? error.message : "Unknown error",
      });
    }
  });
}

