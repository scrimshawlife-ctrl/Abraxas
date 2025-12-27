import type { RuneInvocationContext } from "./ctx.js";

export interface RuneInvocationRecord {
  rune_id: string;
  rune_version: string;
  capability: string;
  ctx: RuneInvocationContext;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown> | null;
  status: string;
  error: string | null;
  timestamp_utc: string;
  ctx_hash: string;
}

export function recordRuneInvocation(
  record: RuneInvocationRecord,
  ledgerPath?: string
): string;
