import crypto from "crypto";
import fs from "fs";
import path from "path";

function sortValue(value) {
  if (Array.isArray(value)) {
    return value.map(sortValue);
  }
  if (value && typeof value === "object") {
    const sorted = {};
    for (const key of Object.keys(value).sort()) {
      sorted[key] = sortValue(value[key]);
    }
    return sorted;
  }
  return value;
}

function hashCanonical(value) {
  const canonical = JSON.stringify(sortValue(value));
  return crypto.createHash("sha256").update(canonical).digest("hex");
}

export function recordRuneInvocation(record, ledgerPath = process.env.ABX_RUNE_LEDGER_PATH) {
  const target = ledgerPath || path.join(".aal", "ledger", "rune_invocations.jsonl");
  const dir = path.dirname(target);
  fs.mkdirSync(dir, { recursive: true });
  const payload = {
    ...record,
    inputs_hash: hashCanonical(record.inputs ?? {}),
    outputs_hash: record.outputs ? hashCanonical(record.outputs) : null,
    ctx_hash: hashCanonical(record.ctx ?? {}),
  };
  payload.ledger_sha256 = hashCanonical(payload);
  fs.appendFileSync(target, `${JSON.stringify(payload)}\n`);
  return payload.ledger_sha256;
}
