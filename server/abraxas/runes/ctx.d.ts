export interface RuneInvocationContext {
  run_id: string;
  subsystem_id: string;
  git_hash: string;
}

export function requireRuneCtx(ctx: RuneInvocationContext | null | undefined): RuneInvocationContext;
export function buildRuneCtx(
  subsystemId: string,
  options?: { runId?: string; gitHash?: string }
): RuneInvocationContext;
