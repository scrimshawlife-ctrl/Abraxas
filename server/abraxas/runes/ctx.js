import crypto from "crypto";
import fs from "fs";
import path from "path";

export function requireRuneCtx(ctx) {
  if (!ctx) {
    throw new Error("Rune invocation ctx is required");
  }
  const { run_id, subsystem_id, git_hash } = ctx;
  if (!run_id || !subsystem_id || !git_hash) {
    throw new Error("Rune invocation ctx missing required fields");
  }
  return ctx;
}

function resolveGitHash() {
  if (process.env.GIT_HASH) {
    return process.env.GIT_HASH;
  }
  const headPath = path.join(process.cwd(), ".git", "HEAD");
  if (!fs.existsSync(headPath)) {
    return "unknown";
  }
  const head = fs.readFileSync(headPath, "utf8").trim();
  if (head.startsWith("ref:")) {
    const refPath = head.split(" ")[1];
    const fullRefPath = path.join(process.cwd(), ".git", refPath);
    if (!fs.existsSync(fullRefPath)) {
      return "unknown";
    }
    return fs.readFileSync(fullRefPath, "utf8").trim();
  }
  return head;
}

export function buildRuneCtx(subsystemId, options = {}) {
  const runId = options.runId || crypto.randomUUID();
  const gitHash = options.gitHash || resolveGitHash();
  return {
    run_id: runId,
    subsystem_id: subsystemId,
    git_hash: gitHash,
  };
}
