export interface RuneBinding {
  runeId: string;
  capability: string;
  name: string;
  version: string;
  deterministic: boolean;
  inputs: string[];
  outputs: string[];
  handler: (input: Record<string, unknown>, ctx: import("./ctx.js").RuneInvocationContext) => unknown;
}

export function getRuneRegistry(): RuneBinding[];
export function listCapabilities(): string[];
export function listRunesByCapability(capability: string): RuneBinding[];
export function describeRune(runeId: string): RuneBinding;
export function wiringSanityCheck(requiredCapabilities?: string[]): {
  duplicateRuneIds: string[];
  missingCapabilities: string[];
};
