import type { RuneInvocationContext } from "./ctx.js";

export function invokeRuneById(
  runeId: string,
  input: Record<string, unknown> | undefined,
  ctx: RuneInvocationContext
): unknown;

export function invokeRuneByCapability(
  capability: string,
  input: Record<string, unknown> | undefined,
  ctx: RuneInvocationContext
): unknown;
