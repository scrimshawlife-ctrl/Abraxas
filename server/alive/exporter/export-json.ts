import { AliveRunResult } from "@shared/alive/schema";

export function exportAsJson(result: AliveRunResult): string {
  return JSON.stringify(result, null, 2);
}
