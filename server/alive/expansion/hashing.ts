import crypto from "crypto";
import type { ProposalRecord } from "./storage";

export function sha256Json(obj: unknown): string {
  const json = JSON.stringify(obj, Object.keys(obj as object).sort(), 0);
  return crypto.createHash("sha256").update(json).digest("hex");
}

export function appendProposalHashes(
  record: ProposalRecord,
  registryHash: string
): ProposalRecord {
  const proposalHash = sha256Json(record.proposal);
  const notes = new Set(record.notes ?? []);
  notes.add(`proposal_hash:${proposalHash}`);
  notes.add(`metric_registry_hash:${registryHash}`);

  return {
    ...record,
    notes: Array.from(notes),
  };
}
