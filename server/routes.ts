import type { Express } from "express";
import { createServer, type Server } from "http";
import { existsSync } from "fs";
import { readFile } from "fs/promises";
import path from "path";
import { storage } from "./storage";
import { setupAuth, isAuthenticated } from "./replitAuth";
import { setupAbraxasRoutes } from "./abraxas-server";
import { setupALIVERoutes } from "./alive/router";
import { registerDashboardRoutes } from "./dashboard/routes";
import {
  insertUserSchema,
  insertTradingConfigSchema,
  insertRitualHistorySchema,
  insertPredictionSchema,
  insertMysticalMetricsSchema,
  insertUserSessionSchema,
  insertIndicatorSchema,
  insertWatchlistSchema,
  insertWatchlistItemSchema
} from "@shared/schema";
import type {
  OperatorProjectionSummary,
  LocalPromotionState,
  FederatedReadinessState,
  PromotionPolicyState,
  RunSummaryView,
  RunDiffSummary,
  ReleaseReadinessView,
  EvidenceView,
} from "@shared/operatorProjection";
import { sql } from "drizzle-orm";
import { registerIndicator, discoverIndicators } from "./indicators";
import { analyzeSymbolPool, updateWatchlistAnalysis } from "./market-analysis";
import rateLimit from "express-rate-limit";
import { setupArtifactLensRoutes } from "./artifacts/routes";
import {
  getComponentRegistry,
  recordComponentApproval,
} from "./governance/component-registry";

// Extend global type for rate limiting
declare global {
  var rateLimitStore: Map<string, number[]>;
}


async function readJsonObject(pathValue: string): Promise<Record<string, unknown> | null> {
  if (!existsSync(pathValue)) return null;
  try {
    const raw = await readFile(pathValue, { encoding: "utf-8" });
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : String(value ?? fallback);
}

function asStringArray(value: unknown, maxItems = 16): string[] {
  return Array.isArray(value) ? value.slice(0, maxItems).map((v: unknown) => String(v)) : [];
}

function asObject(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? value as Record<string, unknown> : {};
}

async function buildOperatorProjectionSummary(runId: string): Promise<OperatorProjectionSummary> {
  const validatorPath = path.resolve(process.cwd(), "out", "validators", `execution-validation-${runId}.json`);
  const localAttestationPath = path.resolve(process.cwd(), "out", "attestation", `canonical_proof_${runId}.json`);
  const promotionAttestationPath = path.resolve(process.cwd(), "out", "attestation", `execution-attestation-${runId}.json`);
  const tier1ProjectionPath = path.resolve(process.cwd(), "out", "operator", `proof_projection_${runId}.json`);

  const validator = await readJsonObject(validatorPath);
  const localAttestation = await readJsonObject(localAttestationPath);
  const promotionAttestation = await readJsonObject(promotionAttestationPath);
  const tier1Projection = await readJsonObject(tier1ProjectionPath);

  const validatorStatus = String(validator?.status ?? "MISSING");
  const localAttestationStatus = String(localAttestation?.overall_status ?? "MISSING");
  const promotionAttestationStatus = String(promotionAttestation?.overall_status ?? "MISSING");

  const proofClosureStatus: "COMPLETE" | "INCOMPLETE" | "NOT_COMPUTABLE" =
    validatorStatus === "VALID" && localAttestationStatus === "PASS"
      ? "COMPLETE"
      : (validatorStatus === "MISSING" || localAttestationStatus === "MISSING" ? "NOT_COMPUTABLE" : "INCOMPLETE");

  const localPromotionState: LocalPromotionState =
    proofClosureStatus !== "COMPLETE"
      ? "NOT_COMPUTABLE"
      : (promotionAttestationStatus === "PASS" ? "LOCAL_PROMOTION_READY" : "LOCAL_ONLY_COMPLETE");

  const federated = asObject(asObject(promotionAttestation).federated);
  const externalRefs = asStringArray(federated.external_attestation_refs);
  const federatedLedgerIds = asStringArray(federated.federated_ledger_ids);
  const remoteValidationStatus = asString(federated.remote_validation_status, "UNAVAILABLE").toUpperCase();
  const remoteAttestationStatus = asString(federated.remote_attestation_status, "UNAVAILABLE").toUpperCase();
  const remoteEvidenceStatus = asString(federated.remote_evidence_status, "NOT_DECLARED").toUpperCase();
  const federatedEvidenceState = asString(federated.federated_evidence_state, "UNKNOWN").toUpperCase();
  const remoteEvidencePacketCount = Number(federated.remote_evidence_packet_count ?? 0) || 0;
  const federatedInconsistency = Boolean(federated.federated_inconsistency);

  const federatedEvidencePresent = externalRefs.length > 0 || federatedLedgerIds.length > 0 || remoteEvidencePacketCount > 0;
  const federatedBlockers: string[] = [];
  if (!federatedEvidencePresent) federatedBlockers.push("missing_external_attestation_refs_and_federated_ledger_ids");
  if (!["VALID", "PASS", "SUCCESS"].includes(remoteValidationStatus)) federatedBlockers.push("remote_validation_not_confirmed");
  if (!["VALID", "PASS", "SUCCESS"].includes(remoteAttestationStatus)) federatedBlockers.push("remote_attestation_not_confirmed");
  if (remoteEvidenceStatus === "MISSING") federatedBlockers.push("remote_evidence_manifest_missing");
  if (remoteEvidenceStatus === "MALFORMED" || federatedEvidenceState === "MALFORMED") federatedBlockers.push("remote_evidence_manifest_malformed");
  if (remoteEvidenceStatus === "INCONSISTENT" || federatedEvidenceState === "INCONSISTENT") federatedBlockers.push("remote_evidence_inconsistent");
  if (remoteEvidenceStatus === "STALE" || federatedEvidenceState === "STALE") federatedBlockers.push("remote_evidence_stale");

  const federatedReadinessState: FederatedReadinessState =
    localPromotionState !== "LOCAL_PROMOTION_READY"
      ? "NOT_COMPUTABLE"
      : (federatedBlockers.length === 0 ? "FEDERATED_READY" : "FEDERATED_INCOMPLETE");


  const promotionPolicyRequiresFederation = true;
  const promotionPolicyReasonCodes: string[] = [];
  let promotionPolicyState: PromotionPolicyState = "BLOCKED";
  if (localPromotionState !== "LOCAL_PROMOTION_READY") {
    promotionPolicyReasonCodes.push("local_promotion_not_ready");
    promotionPolicyState = proofClosureStatus === "NOT_COMPUTABLE" ? "NOT_COMPUTABLE" : "BLOCKED";
  } else if (promotionPolicyRequiresFederation && federatedReadinessState !== "FEDERATED_READY") {
    if (remoteEvidenceStatus === "MISSING") {
      promotionPolicyReasonCodes.push("federated_remote_evidence_missing");
    } else if (remoteEvidenceStatus === "MALFORMED" || federatedEvidenceState === "MALFORMED") {
      promotionPolicyReasonCodes.push("federated_remote_evidence_malformed");
    } else if (remoteEvidenceStatus === "INCONSISTENT" || federatedEvidenceState === "INCONSISTENT") {
      promotionPolicyReasonCodes.push("federated_remote_evidence_inconsistent");
    } else if (remoteEvidenceStatus === "STALE" || federatedEvidenceState === "STALE") {
      promotionPolicyReasonCodes.push("federated_remote_evidence_stale");
    } else if (remoteEvidenceStatus === "PARTIAL" || federatedEvidenceState === "PARTIAL") {
      promotionPolicyReasonCodes.push("federated_remote_evidence_partial");
    } else {
      promotionPolicyReasonCodes.push("federated_readiness_required");
    }
    promotionPolicyState = "BLOCKED";
  } else {
    promotionPolicyReasonCodes.push("policy_requirements_satisfied");
    promotionPolicyState = "ALLOWED";
  }

  const validatorCorrelation = asObject(asObject(validator).correlation);
  const pointers = asStringArray(validatorCorrelation.pointers, 20);

  return {
    schema: "OperatorProjectionSummary.v1",
    run_id: runId,
    generated_at: new Date().toISOString(),
    tier1_local_closure: proofClosureStatus === "COMPLETE" ? "PASS" : proofClosureStatus,
    tier2_local_promotion_state: localPromotionState,
    tier25_federated_readiness_state: federatedReadinessState,
    validator_status: validatorStatus,
    local_attestation_status: localAttestationStatus,
    promotion_attestation_status: promotionAttestationStatus,
    proof_closure_status: proofClosureStatus,
    federated_evidence_present: federatedEvidencePresent,
    federated_evidence_state_summary: federatedEvidenceState as OperatorProjectionSummary["federated_evidence_state_summary"],
    remote_evidence_packet_count: remoteEvidencePacketCount,
    federated_inconsistency_flag: federatedInconsistency,
    promotion_policy_state: promotionPolicyState,
    promotion_policy_reason_codes: promotionPolicyReasonCodes.slice(0, 8),
    promotion_policy_requires_federation: promotionPolicyRequiresFederation,
    promotion_policy_waived: false,
    federated_blockers: federatedBlockers.slice(0, 8),
    linkage: {
      has_validator: existsSync(validatorPath),
      has_local_attestation: existsSync(localAttestationPath),
      has_promotion_attestation: existsSync(promotionAttestationPath),
      has_tier1_projection: existsSync(tier1ProjectionPath),
      correlation_pointer_count: pointers.length,
      correlation_pointers: pointers,
      key_artifact_ids: {
        validator_artifact_id: asString(asObject(validator).artifactId, "MISSING"),
        tier1_projection_artifact_type: asString(asObject(tier1Projection).artifactType, "MISSING"),
      },
    },
    artifacts: {
      validator: validatorPath,
      local_attestation: localAttestationPath,
      promotion_attestation: promotionAttestationPath,
      tier1_projection: tier1ProjectionPath,
    },
    provenance: {
      source: "server.routes.buildOperatorProjectionSummary",
      note: "TS secondary projection aligned to canonical OperatorProjectionSummary.v1 semantics",
    },
  };
}

function flattenBlockers(...values: unknown[]): string[] {
  const merged = values.flatMap((value) => asStringArray(value, 24));
  return Array.from(new Set(merged)).slice(0, 24);
}

async function buildEvidenceView(runId: string): Promise<EvidenceView> {
  const promotionAttestationPath = path.resolve(process.cwd(), "out", "attestation", `execution-attestation-${runId}.json`);
  const promotionAttestation = await readJsonObject(promotionAttestationPath);
  const federated = asObject(asObject(promotionAttestation).federated);

  return {
    run_id: runId,
    federated_evidence_state_summary: asString(federated.federated_evidence_state, "UNKNOWN") as EvidenceView["federated_evidence_state_summary"],
    remote_evidence_packet_count: Number(federated.remote_evidence_packet_count ?? 0) || 0,
    inconsistency_flag: Boolean(federated.federated_inconsistency),
    manifest_validation_outcome: asString(federated.remote_evidence_status, "NOT_DECLARED"),
    origin: asString(federated.remote_evidence_origin, ""),
    packet_list: [],
    blockers: asStringArray(federated.blockers, 16),
  };
}

async function buildRunSummaryView(runId: string): Promise<RunSummaryView> {
  const projection = await buildOperatorProjectionSummary(runId);
  const policyPath = path.resolve(process.cwd(), "out", "policy", `promotion-policy-${runId}.json`);
  const readinessPath = path.resolve(process.cwd(), "out", "promotion", `promotion-readiness-${runId}.json`);
  const executionPath = path.resolve(process.cwd(), "out", "attestation", `execution-attestation-${runId}.json`);

  const policy = await readJsonObject(policyPath);
  const readiness = await readJsonObject(readinessPath);
  const execution = await readJsonObject(executionPath);
  const evidence = await buildEvidenceView(runId);

  const executionStatus = {
    status: execution ? "PRESENT" : "MISSING",
    overall_status: asString(asObject(execution).overall_status, "MISSING"),
    policy_decision_state: asString(asObject(asObject(execution).policy_gate).decision_state, "UNKNOWN"),
    fail_reasons: asStringArray(asObject(execution).fail_reasons, 8),
    artifact: executionPath,
  };

  return {
    run_id: runId,
    projection_summary: projection,
    policy_state: asString(policy?.decision_state ?? projection.promotion_policy_state, "UNKNOWN"),
    readiness_state: {
      status: asString(readiness?.status, "UNKNOWN"),
      local_promotion_state: asString(readiness?.local_promotion_state, "UNKNOWN"),
      federated_readiness_state: asString(readiness?.federated_readiness_state, "UNKNOWN"),
    },
    federated_summary: {
      federated_evidence_state_summary: evidence.federated_evidence_state_summary,
      remote_evidence_packet_count: evidence.remote_evidence_packet_count,
      inconsistency_flag: evidence.inconsistency_flag,
      manifest_validation_outcome: evidence.manifest_validation_outcome,
    },
    execution_status: executionStatus,
    blockers: flattenBlockers(
      projection.federated_blockers,
      asObject(policy).blockers,
      asObject(asObject(readiness).federated_evidence).blockers,
      executionStatus.fail_reasons,
    ),
    artifact_refs: Array.from(new Set([
      projection.artifacts.validator,
      projection.artifacts.local_attestation,
      projection.artifacts.promotion_attestation,
      asString(asObject(policy).artifacts ? asObject(asObject(policy).artifacts).waiver : "", ""),
      executionPath,
    ].filter((item) => String(item).trim().length > 0))).slice(0, 12).map((v) => String(v)),
  };
}

async function buildRunDiffSummary(runA: string, runB: string): Promise<RunDiffSummary> {
  const left = await buildRunSummaryView(runA);
  const right = await buildRunSummaryView(runB);
  const changedFields = ["policy_state", "readiness_state", "federated_summary", "execution_status", "blockers"]
    .filter((key) => JSON.stringify(left[key as keyof RunSummaryView]) !== JSON.stringify(right[key as keyof RunSummaryView]));
  const leftBlockers = new Set(left.blockers);
  const rightBlockers = new Set(right.blockers);
  return {
    run_a: runA,
    run_b: runB,
    changed_fields: changedFields,
    policy_delta: { from: String(left.policy_state), to: String(right.policy_state) },
    readiness_delta: { from: left.readiness_state, to: right.readiness_state },
    federated_delta: {
      from: left.federated_summary as Record<string, unknown>,
      to: right.federated_summary as Record<string, unknown>,
      new_blockers: Array.from(rightBlockers).filter((item) => !leftBlockers.has(item)).sort(),
      cleared_blockers: Array.from(leftBlockers).filter((item) => !rightBlockers.has(item)).sort(),
    },
    execution_delta: { from: left.execution_status, to: right.execution_status },
  };
}

async function buildReleaseReadinessView(runId: string): Promise<ReleaseReadinessView> {
  const releasePath = path.resolve(process.cwd(), "out", "release", `release-readiness-${runId}.json`);
  const report = await readJsonObject(releasePath);
  const checks = Array.isArray(report?.checks) ? report.checks : [];
  return {
    run_id: runId,
    status: asString(report?.status, "NOT_READY"),
    blocking_issues: asStringArray(report?.blocking_failures, 16),
    non_blocking_issues: asStringArray(report?.known_non_blocking, 16),
    checklist: checks.slice(0, 24).map((item: unknown) => {
      const obj = asObject(item);
      return {
        name: asString(obj.name, "unknown"),
        outcome: asString(obj.outcome, "UNKNOWN"),
        ok: Boolean(obj.ok),
        notes: asString(obj.notes, "").slice(0, 240),
      };
    }),
  };
}


export async function registerRoutes(app: Express): Promise<Server> {
  // Create HTTP server
  const httpServer = createServer(app);

  // Read-only artifact dashboard endpoints (no auth, no writes)
  setupArtifactLensRoutes(app);

  // Rate limiting for authentication endpoints
  const authRateLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 5, // Limit each IP to 5 login requests per window
    message: { error: "Too many authentication attempts, please try again later" },
    standardHeaders: true,
    legacyHeaders: false,
  });

  // Setup authentication with rate limiting
  await setupAuth(app, authRateLimiter);

  // Setup Abraxas mystical trading routes
  setupAbraxasRoutes(app, httpServer);

  // Setup ALIVE routes
  setupALIVERoutes(app);

  // Filesystem-backed dashboard API (read-only)
  registerDashboardRoutes(app);

  // Auth endpoint
  app.get('/api/auth/user', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const user = await storage.getUser(userId);
      res.json(user);
    } catch (error) {
      console.error("Error fetching user:", error);
      res.status(500).json({ message: "Failed to fetch user" });
    }
  });

  // Health endpoints
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", timestamp: Date.now(), service: "Abraxas Trading Oracle" });
  });

  // Secondary TS projection route aligned to canonical operator summary contract
  app.get("/api/operator/projection/:runId", isAuthenticated, async (req, res) => {
    try {
      const summary = await buildOperatorProjectionSummary(String(req.params.runId));
      res.json(summary);
    } catch (error) {
      console.error("Error building operator projection summary:", error);
      res.status(500).json({ error: "projection_summary_failed" });
    }
  });

  app.get("/api/operator/run/:runId", isAuthenticated, async (req, res) => {
    try {
      const payload = await buildRunSummaryView(String(req.params.runId));
      res.json(payload);
    } catch (error) {
      console.error("Error building run summary view:", error);
      res.status(500).json({ error: "run_summary_failed" });
    }
  });

  app.get("/api/operator/compare/:runA/:runB", isAuthenticated, async (req, res) => {
    try {
      const payload = await buildRunDiffSummary(String(req.params.runA), String(req.params.runB));
      res.json(payload);
    } catch (error) {
      console.error("Error building run diff summary:", error);
      res.status(500).json({ error: "run_diff_failed" });
    }
  });

  app.get("/api/operator/release-readiness/:runId", isAuthenticated, async (req, res) => {
    try {
      const payload = await buildReleaseReadinessView(String(req.params.runId));
      res.json(payload);
    } catch (error) {
      console.error("Error building release readiness view:", error);
      res.status(500).json({ error: "release_readiness_failed" });
    }
  });

  app.get("/api/operator/evidence/:runId", isAuthenticated, async (req, res) => {
    try {
      const payload = await buildEvidenceView(String(req.params.runId));
      res.json(payload);
    } catch (error) {
      console.error("Error building evidence view:", error);
      res.status(500).json({ error: "evidence_view_failed" });
    }
  });

  // Acceptance truth panel (artifact-only, read-only)
  app.get("/api/acceptance/status", isAuthenticated, async (_req, res) => {
    try {
      const p = path.resolve(process.cwd(), "out", "acceptance", "acceptance_status_v1.json");
      if (!existsSync(p)) {
        return res.status(404).json({ error: "not_found" });
      }
      const raw = await readFile(p, { encoding: "utf-8" });
      res.json(JSON.parse(raw));
    } catch (error) {
      console.error("Error reading acceptance status:", error);
      res.status(500).json({ error: "read_failed" });
    }
  });

  app.get("/api/acceptance/drift", isAuthenticated, async (_req, res) => {
    try {
      const p = path.resolve(process.cwd(), "out", "acceptance", "drift_on_failure_v1.json");
      if (!existsSync(p)) {
        return res.status(404).json({ error: "not_found" });
      }
      const raw = await readFile(p, { encoding: "utf-8" });
      res.json(JSON.parse(raw));
    } catch (error) {
      console.error("Error reading acceptance drift:", error);
      res.status(500).json({ error: "read_failed" });
    }
  });

  // Governance registry
  app.get("/api/governance/component-registry", isAuthenticated, async (_req, res) => {
    try {
      const registry = await getComponentRegistry();
      res.json(registry);
    } catch (error) {
      console.error("Error building component registry:", error);
      res.status(500).json({ error: "registry_failed" });
    }
  });

  app.post("/api/governance/component-approvals", isAuthenticated, async (req: any, res) => {
    const { module, decision, reason } = req.body ?? {};
    if (!module || typeof module !== "string") {
      return res.status(400).json({ error: "invalid_module" });
    }
    if (!decision || typeof decision !== "string") {
      return res.status(400).json({ error: "invalid_decision" });
    }
    const allowedDecisions = ["approved", "needs-review", "rejected"] as const;
    if (!allowedDecisions.includes(decision as typeof allowedDecisions[number])) {
      return res.status(400).json({ error: "invalid_decision" });
    }
    const reviewer =
      req.user?.claims?.email ??
      req.user?.claims?.sub ??
      req.user?.email ??
      "unknown";
    try {
      const approvals = await recordComponentApproval({
        module,
        decision: decision as typeof allowedDecisions[number],
        reviewer,
        reason: typeof reason === "string" ? reason : "",
      });
      res.json({ ok: true, approvals: approvals.approvals });
    } catch (error) {
      console.error("Error recording component approval:", error);
      res.status(500).json({ error: "approval_failed" });
    }
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

  app.get("/api/config", isAuthenticated, (req, res) => {
    res.json({ 
      weights: configStore, 
      defaults: configStore
    });
  });

  app.post("/api/config", isAuthenticated, (req, res) => {
    const { weights } = req.body || {};
    if (!weights || typeof weights !== "object") {
      return res.status(400).json({ error: "invalid_payload" });
    }
    // Update in-memory store
    configStore = { ...configStore, ...weights };
    res.json({ ok: true, weights: configStore });
  });

  // Config preview - test weights without persisting
  app.post("/api/config/preview", isAuthenticated, (req, res) => {
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
      impact_summary: `Adjusted ${Object.keys(weights).length} weights. Primary influences: ${Object.entries(weights).slice(0,3).map(([k,v]) => `${k}(${typeof v === 'number' && v > 0 ? '+' : ''}${typeof v === 'number' ? v.toFixed(2) : v})`).join(', ')}`
    };

    res.json({ 
      previewed: weights, 
      results: previewResults 
    });
  });

  // User routes
  app.post("/api/users", async (req, res) => {
    try {
      const userData = insertUserSchema.parse(req.body);
      const user = await storage.createUser(userData);
      res.json(user);
    } catch (error) {
      res.status(400).json({ error: "Invalid user data" });
    }
  });

  app.get("/api/users/:username", async (req, res) => {
    try {
      const user = await storage.getUserByUsername(req.params.username);
      if (!user) {
        return res.status(404).json({ error: "User not found" });
      }
      res.json(user);
    } catch (error) {
      res.status(500).json({ error: "Internal server error" });
    }
  });

  // Trading Configuration routes
  app.get("/api/trading-configs", async (req, res) => {
    try {
      const { userId } = req.query;
      const configs = await storage.getTradingConfigs(userId as string);
      res.json(configs);
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve trading configs" });
    }
  });

  app.get("/api/trading-configs/:id", async (req, res) => {
    try {
      const config = await storage.getTradingConfig(req.params.id);
      if (!config) {
        return res.status(404).json({ error: "Trading config not found" });
      }
      res.json(config);
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve trading config" });
    }
  });

  app.post("/api/trading-configs", async (req, res) => {
    try {
      const configData = insertTradingConfigSchema.parse(req.body);
      const config = await storage.createTradingConfig(configData);
      res.json(config);
    } catch (error) {
      res.status(400).json({ error: "Invalid trading config data" });
    }
  });

  app.patch("/api/trading-configs/:id", async (req, res) => {
    try {
      const updateData = insertTradingConfigSchema.partial().parse(req.body);
      const config = await storage.updateTradingConfig(req.params.id, updateData);
      if (!config) {
        return res.status(404).json({ error: "Trading config not found" });
      }
      res.json(config);
    } catch (error) {
      res.status(400).json({ error: "Invalid trading config update data" });
    }
  });

  app.delete("/api/trading-configs/:id", async (req, res) => {
    try {
      const deleted = await storage.deleteTradingConfig(req.params.id);
      if (!deleted) {
        return res.status(404).json({ error: "Trading config not found" });
      }
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to delete trading config" });
    }
  });

  // Ritual History routes
  app.get("/api/ritual-history", async (req, res) => {
    try {
      const { userId, limit } = req.query;
      const rituals = await storage.getRitualHistory(
        userId as string, 
        limit ? parseInt(limit as string) : undefined
      );
      res.json(rituals);
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve ritual history" });
    }
  });

  app.post("/api/ritual-history", async (req, res) => {
    try {
      const ritualData = insertRitualHistorySchema.parse(req.body);
      const ritual = await storage.createRitualHistory(ritualData);
      res.json(ritual);
    } catch (error) {
      res.status(400).json({ error: "Invalid ritual history data" });
    }
  });

  app.patch("/api/ritual-history/:id/status", async (req, res) => {
    try {
      const { status, results } = req.body;
      const ritual = await storage.updateRitualStatus(req.params.id, status, results);
      if (!ritual) {
        return res.status(404).json({ error: "Ritual not found" });
      }
      res.json(ritual);
    } catch (error) {
      res.status(400).json({ error: "Failed to update ritual status" });
    }
  });

  // Predictions routes
  app.get("/api/predictions", async (req, res) => {
    try {
      const { userId, isResolved } = req.query;
      const predictions = await storage.getPredictions(
        userId as string,
        isResolved ? isResolved === 'true' : undefined
      );
      res.json(predictions);
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve predictions" });
    }
  });

  app.post("/api/predictions", async (req, res) => {
    try {
      const predictionData = insertPredictionSchema.parse(req.body);
      const prediction = await storage.createPrediction(predictionData);
      res.json(prediction);
    } catch (error) {
      res.status(400).json({ error: "Invalid prediction data" });
    }
  });

  app.patch("/api/predictions/:id/resolve", async (req, res) => {
    try {
      const { actualValue, accuracy } = req.body;
      const prediction = await storage.resolvePrediction(req.params.id, actualValue, accuracy);
      if (!prediction) {
        return res.status(404).json({ error: "Prediction not found" });
      }
      res.json(prediction);
    } catch (error) {
      res.status(400).json({ error: "Failed to resolve prediction" });
    }
  });

  // Mystical Metrics routes
  app.get("/api/mystical-metrics", async (req, res) => {
    try {
      const { userId, metricType, period } = req.query;
      const metrics = await storage.getMysticalMetrics(
        userId as string,
        metricType as string,
        period as string
      );
      res.json(metrics);
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve mystical metrics" });
    }
  });

  app.post("/api/mystical-metrics", async (req, res) => {
    try {
      const metricsData = insertMysticalMetricsSchema.parse(req.body);
      const metrics = await storage.createMysticalMetrics(metricsData);
      res.json(metrics);
    } catch (error) {
      res.status(400).json({ error: "Invalid mystical metrics data" });
    }
  });

  // User Sessions routes
  app.get("/api/user-sessions/:userId", async (req, res) => {
    try {
      const { limit } = req.query;
      const sessions = await storage.getUserSessions(
        req.params.userId,
        limit ? parseInt(limit as string) : undefined
      );
      res.json(sessions);
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve user sessions" });
    }
  });

  app.post("/api/user-sessions", async (req, res) => {
    try {
      const sessionData = insertUserSessionSchema.parse(req.body);
      const session = await storage.createUserSession(sessionData);
      res.json(session);
    } catch (error) {
      res.status(400).json({ error: "Invalid user session data" });
    }
  });

  app.patch("/api/user-sessions/:id/end", async (req, res) => {
    try {
      const { outcome, actions } = req.body;
      const session = await storage.endUserSession(req.params.id, outcome, actions);
      if (!session) {
        return res.status(404).json({ error: "User session not found" });
      }
      res.json(session);
    } catch (error) {
      res.status(400).json({ error: "Failed to end user session" });
    }
  });

  // Enhanced Abraxas status endpoint with database info
  app.get("/api/abraxas/status", (req, res) => {
    res.json({ 
      status: "active", 
      mystical_alignment: 0.873,
      database: "postgresql",
      tables_count: 6,
      runes: "⟟Σ Active Σ⟟"
    });
  });

  // Debug endpoint to verify database connection and table counts
  app.get("/api/debug/db-info", async (req, res) => {
    try {
      const { db } = require("./db");
      const { users, tradingConfigs, ritualHistory, predictions, mysticalMetrics, userSessions } = require("@shared/schema");
      
      // Get database info without exposing credentials
      const dbUrl = process.env.DATABASE_URL || "";
      const dbHost = dbUrl.includes("@") ? dbUrl.split("@")[1]?.split("/")[0] : "localhost";
      
      // Count records in each table
      const [
        userCount,
        configCount, 
        ritualCount,
        predictionCount,
        metricCount,
        sessionCount
      ] = await Promise.all([
        db.select({ count: sql`count(*)` }).from(users),
        db.select({ count: sql`count(*)` }).from(tradingConfigs),
        db.select({ count: sql`count(*)` }).from(ritualHistory),
        db.select({ count: sql`count(*)` }).from(predictions), 
        db.select({ count: sql`count(*)` }).from(mysticalMetrics),
        db.select({ count: sql`count(*)` }).from(userSessions)
      ]);

      res.json({
        database_host: dbHost,
        connection_status: "active",
        table_counts: {
          users: parseInt(userCount[0]?.count || "0"),
          trading_configs: parseInt(configCount[0]?.count || "0"),
          ritual_history: parseInt(ritualCount[0]?.count || "0"),
          predictions: parseInt(predictionCount[0]?.count || "0"),
          mystical_metrics: parseInt(metricCount[0]?.count || "0"),
          user_sessions: parseInt(sessionCount[0]?.count || "0")
        },
        timestamp: Date.now()
      });
    } catch (error) {
      console.error("Database debug error:", error);
      res.status(500).json({ 
        error: "Database connection failed", 
        details: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  // Indicator API routes
  app.get("/api/indicators", async (req, res) => {
    try {
      const indicators = await storage.getAllIndicators();
      res.json({ items: indicators });
    } catch (error) {
      res.status(500).json({ error: "Failed to retrieve indicators" });
    }
  });

  // Manual register (requires validation). Keep path obscure.
  app.post("/api/indicators/_register", async (req, res) => {
    try {
      // Rate limit check (simple in-memory implementation)
      const clientIP = req.ip || req.connection.remoteAddress || 'unknown';
      const rateLimitKey = `register_${clientIP}`;
      const now = Date.now();
      const RATE_LIMIT_WINDOW = 60 * 1000; // 1 minute
      const RATE_LIMIT_MAX = 5; // max 5 requests per minute
      
      if (!global.rateLimitStore) {
        global.rateLimitStore = new Map();
      }
      
      const requests = global.rateLimitStore.get(rateLimitKey) || [];
      const recentRequests = requests.filter((time: number) => now - time < RATE_LIMIT_WINDOW);
      
      if (recentRequests.length >= RATE_LIMIT_MAX) {
        return res.status(429).json({ error: "Rate limit exceeded. Try again later." });
      }
      
      recentRequests.push(now);
      global.rateLimitStore.set(rateLimitKey, recentRequests);

      // Validate request body with basic checks first
      const { name, slug } = req.body || {};
      if (!name || !slug) {
        return res.status(400).json({ error: "missing_name_or_slug" });
      }

      // Validate slug format separately before passing to registerIndicator
      const slugRegex = /^[a-z0-9-]{1,64}$/;
      if (!slugRegex.test(slug)) {
        return res.status(400).json({ 
          error: "invalid_slug", 
          details: "Slug must be alphanumeric with dashes, 1-64 characters" 
        });
      }

      // Validate name length
      if (name.length < 1 || name.length > 128) {
        return res.status(400).json({ 
          error: "invalid_name", 
          details: "Name must be 1-128 characters" 
        });
      }

      // Call registerIndicator to get proper SVG generation and config updates
      const rec = await registerIndicator({ name, slug });
      
      res.json({ ok: true, indicator: rec });
    } catch (error) {
      if (error instanceof Error && error.message.includes("unique constraint")) {
        res.status(409).json({ error: "Indicator with this key already exists" });
      } else {
        res.status(500).json({ error: "Failed to register indicator" });
      }
    }
  });

  // Trigger discovery now (restricted endpoint)
  app.post("/api/indicators/discover", async (req, res) => {
    try {
      // Rate limit check for discovery endpoint
      const clientIP = req.ip || req.connection.remoteAddress || 'unknown';
      const rateLimitKey = `discover_${clientIP}`;
      const now = Date.now();
      const RATE_LIMIT_WINDOW = 5 * 60 * 1000; // 5 minutes
      const RATE_LIMIT_MAX = 3; // max 3 requests per 5 minutes
      
      if (!global.rateLimitStore) {
        global.rateLimitStore = new Map();
      }
      
      const requests = global.rateLimitStore.get(rateLimitKey) || [];
      const recentRequests = requests.filter((time: number) => now - time < RATE_LIMIT_WINDOW);
      
      if (recentRequests.length >= RATE_LIMIT_MAX) {
        return res.status(429).json({ error: "Rate limit exceeded. Discovery is resource intensive." });
      }
      
      recentRequests.push(now);
      global.rateLimitStore.set(rateLimitKey, recentRequests);

      const minted = await discoverIndicators();
      res.json({ ok: true, minted });
    } catch (error) {
      res.status(500).json({ error: "Failed to discover indicators" });
    }
  });

  // ============================================================================
  // DYNAMIC WATCHLIST API ENDPOINTS
  // ============================================================================

  // Get all watchlists for authenticated user
  app.get("/api/watchlists", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const watchlists = await storage.getWatchlists(userId);
      res.json({ watchlists });
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch watchlists" });
    }
  });

  // Get specific watchlist with items (authenticated)
  app.get("/api/watchlists/:id", isAuthenticated, async (req: any, res) => {
    try {
      const { id } = req.params;
      const userId = req.user.claims.sub;
      const watchlist = await storage.getWatchlistById(id);
      
      if (!watchlist || watchlist.userId !== userId) {
        return res.status(404).json({ error: "Watchlist not found" });
      }
      
      const items = await storage.getWatchlistItems(id);
      res.json({ watchlist, items });
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch watchlist" });
    }
  });

  // Create new watchlist (authenticated)
  app.post("/api/watchlists", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const validation = insertWatchlistSchema.safeParse({
        ...req.body,
        userId
      });
      
      if (!validation.success) {
        return res.status(400).json({ 
          error: "validation_failed", 
          details: validation.error.errors 
        });
      }
      
      const watchlist = await storage.createWatchlist(validation.data);
      res.status(201).json({ watchlist });
    } catch (error) {
      res.status(500).json({ error: "Failed to create watchlist" });
    }
  });

  // Update watchlist
  app.put("/api/watchlists/:id", async (req, res) => {
    try {
      const { id } = req.params;
      const validation = insertWatchlistSchema.partial().safeParse(req.body);
      
      if (!validation.success) {
        return res.status(400).json({ 
          error: "validation_failed", 
          details: validation.error.errors 
        });
      }
      
      const watchlist = await storage.updateWatchlist(id, validation.data);
      
      if (!watchlist) {
        return res.status(404).json({ error: "Watchlist not found" });
      }
      
      res.json({ watchlist });
    } catch (error) {
      res.status(500).json({ error: "Failed to update watchlist" });
    }
  });

  // Delete watchlist
  app.delete("/api/watchlists/:id", async (req, res) => {
    try {
      const { id } = req.params;
      const success = await storage.deleteWatchlist(id);
      
      if (!success) {
        return res.status(404).json({ error: "Watchlist not found" });
      }
      
      res.json({ ok: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to delete watchlist" });
    }
  });

  // Get watchlist items (authenticated)
  app.get("/api/watchlists/:id/items", isAuthenticated, async (req: any, res) => {
    try {
      const { id } = req.params;
      const userId = req.user.claims.sub;
      
      // Verify the watchlist belongs to the authenticated user
      const watchlist = await storage.getWatchlistById(id);
      if (!watchlist || watchlist.userId !== userId) {
        return res.status(404).json({ error: "Watchlist not found" });
      }
      
      const items = await storage.getWatchlistItems(id);
      res.json(items);
    } catch (error) {
      console.error("Get watchlist items error:", error);
      res.status(500).json({ error: "Failed to get watchlist items" });
    }
  });

  // Add item to watchlist
  app.post("/api/watchlists/:id/items", async (req, res) => {
    try {
      const { id } = req.params;
      const validation = insertWatchlistItemSchema.safeParse({
        ...req.body,
        watchlistId: id
      });
      
      if (!validation.success) {
        return res.status(400).json({ 
          error: "validation_failed", 
          details: validation.error.errors 
        });
      }
      
      const item = await storage.addWatchlistItem(validation.data);
      res.status(201).json({ item });
    } catch (error) {
      res.status(500).json({ error: "Failed to add item to watchlist" });
    }
  });

  // Update watchlist item
  app.put("/api/watchlists/:watchlistId/items/:itemId", async (req, res) => {
    try {
      const { itemId } = req.params;
      const validation = insertWatchlistItemSchema.partial().safeParse(req.body);
      
      if (!validation.success) {
        return res.status(400).json({ 
          error: "validation_failed", 
          details: validation.error.errors 
        });
      }
      
      const item = await storage.updateWatchlistItem(itemId, validation.data);
      
      if (!item) {
        return res.status(404).json({ error: "Watchlist item not found" });
      }
      
      res.json({ item });
    } catch (error) {
      res.status(500).json({ error: "Failed to update watchlist item" });
    }
  });

  // Remove item from watchlist
  app.delete("/api/watchlists/:watchlistId/items/:itemId", async (req, res) => {
    try {
      const { itemId } = req.params;
      const success = await storage.removeWatchlistItem(itemId);
      
      if (!success) {
        return res.status(404).json({ error: "Watchlist item not found" });
      }
      
      res.json({ ok: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to remove item from watchlist" });
    }
  });

  // Analyze symbols and suggest candidates for watchlist
  app.post("/api/watchlists/analyze", async (req, res) => {
    try {
      const { symbols, analysisType, limit = 10 } = req.body;
      
      if (!symbols || !Array.isArray(symbols)) {
        return res.status(400).json({ error: "symbols array is required" });
      }
      
      if (!analysisType || !["growth", "short"].includes(analysisType)) {
        return res.status(400).json({ error: "analysisType must be 'growth' or 'short'" });
      }
      
      // Validate symbol format
      for (const item of symbols) {
        if (!item.symbol || !item.type || !["equity", "fx"].includes(item.type)) {
          return res.status(400).json({ 
            error: "Each symbol must have 'symbol' and 'type' ('equity' or 'fx')" 
          });
        }
      }
      
      const candidates = await analyzeSymbolPool(symbols, analysisType, limit);
      res.json({ candidates, analysisType });
    } catch (error) {
      res.status(500).json({ error: "Failed to analyze symbols" });
    }
  });

  // Refresh analysis for watchlist
  app.post("/api/watchlists/:id/refresh", async (req, res) => {
    try {
      const { id } = req.params;
      await updateWatchlistAnalysis(id);
      
      // Return updated watchlist with items
      const watchlist = await storage.getWatchlistById(id);
      const items = await storage.getWatchlistItems(id);
      
      res.json({ watchlist, items, refreshed: true });
    } catch (error) {
      if (error instanceof Error && error.message === "Watchlist not found") {
        return res.status(404).json({ error: "Watchlist not found" });
      }
      res.status(500).json({ error: "Failed to refresh watchlist analysis" });
    }
  });

  // Automatically generate growth/short watchlists (authenticated)
  app.post("/api/watchlists/auto-generate", isAuthenticated, async (req: any, res) => {
    console.log("Auto-generate endpoint called with body:", req.body);
    try {
      const userId = req.user.claims.sub; // Get user ID from authenticated session
      const { analysisType = "growth", symbolPool, limit = 10 } = req.body;
      
      
      if (!["growth", "short"].includes(analysisType)) {
        return res.status(400).json({ error: "analysisType must be 'growth' or 'short'" });
      }
      
      // Default symbol pool if not provided
      const defaultSymbolPool = [
        { symbol: "AAPL", type: "equity" }, { symbol: "MSFT", type: "equity" },
        { symbol: "GOOGL", type: "equity" }, { symbol: "TSLA", type: "equity" },
        { symbol: "NVDA", type: "equity" }, { symbol: "AMZN", type: "equity" },
        { symbol: "META", type: "equity" }, { symbol: "JPM", type: "equity" },
        { symbol: "EURUSD", type: "fx" }, { symbol: "GBPUSD", type: "fx" },
        { symbol: "USDJPY", type: "fx" }, { symbol: "AUDUSD", type: "fx" }
      ];
      
      const symbols = symbolPool || defaultSymbolPool;
      
      // Check if user already has a watchlist of this type
      let watchlist = await storage.getWatchlistByType(userId, analysisType);
      
      if (!watchlist) {
        // Create new watchlist
        watchlist = await storage.createWatchlist({
          userId,
          name: analysisType === "growth" ? "Growth Opportunities" : "Short Candidates",
          type: analysisType,
          description: `Automatically generated ${analysisType} watchlist based on market analysis`
        });
      }
      
      // Clear existing items
      const existingItems = await storage.getWatchlistItems(watchlist.id);
      for (const item of existingItems) {
        await storage.removeWatchlistItem(item.id);
      }
      
      // Analyze symbols and add top candidates
      console.log("About to call analyzeSymbolPool with:", { symbols: symbols.length, analysisType, limit });
      const candidates = await analyzeSymbolPool(symbols, analysisType, limit);
      console.log("AnalyzeSymbolPool returned:", candidates.length, "candidates");
      
      for (const candidate of candidates) {
        await storage.addWatchlistItem({
          watchlistId: watchlist.id,
          symbol: candidate.symbol,
          symbolType: candidate.symbolType,
          analysisScore: candidate.analysisScore,
          confidence: candidate.confidence,
          growthPotential: candidate.growthPotential,
          shortPotential: candidate.shortPotential,
          riskLevel: candidate.riskLevel,
          sector: candidate.sector,
          rationale: candidate.rationale,
          metadata: candidate.metadata
        });
      }
      
      // Update watchlist analysis timestamp
      await storage.updateWatchlist(watchlist.id, {
        lastAnalyzed: new Date()
      });
      
      const items = await storage.getWatchlistItems(watchlist.id);
      res.json({ watchlist, items, generated: true });
    } catch (error) {
      console.error("Auto-generate watchlist error:", error);
      res.status(500).json({ 
        error: "Failed to auto-generate watchlist",
        details: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  return httpServer;
}
