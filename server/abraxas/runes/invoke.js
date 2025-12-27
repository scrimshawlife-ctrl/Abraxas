import { requireRuneCtx } from "./ctx.js";
import { describeRune, listRunesByCapability } from "./registry.js";
import { recordRuneInvocation } from "./ledger.js";

export function invokeRuneById(runeId, input = {}, ctx) {
  const context = requireRuneCtx(ctx);
  const binding = describeRune(runeId);
  const timestamp = new Date().toISOString();

  try {
    const outputs = binding.handler(input, context);
    recordRuneInvocation({
      rune_id: binding.runeId,
      rune_version: binding.version,
      capability: binding.capability,
      ctx: context,
      inputs: input,
      outputs,
      status: "ok",
      error: null,
      timestamp_utc: timestamp,
    });
    return outputs;
  } catch (error) {
    recordRuneInvocation({
      rune_id: binding.runeId,
      rune_version: binding.version,
      capability: binding.capability,
      ctx: context,
      inputs: input,
      outputs: null,
      status: "failed",
      error: String(error),
      timestamp_utc: timestamp,
    });
    throw error;
  }
}

export function invokeRuneByCapability(capability, input = {}, ctx) {
  const matches = listRunesByCapability(capability);
  if (matches.length === 0) {
    throw new Error(`No rune registered for capability: ${capability}`);
  }
  if (matches.length > 1) {
    throw new Error(`Multiple runes registered for capability: ${capability}`);
  }
  return invokeRuneById(matches[0].runeId, input, ctx);
}
