import fs from "fs";
import path from "path";

export interface PromotePlan {
  metric_id: string;
  new_status: "promoted";
  new_version: string;
  notes?: string[];
}

export function writePromotionPatch(plan: PromotePlan): string {
  const patch = {
    kind: "ALIVE_METRIC_PROMOTION_PATCH",
    created_at: new Date().toISOString(),
    plan,
  };
  const outDir = path.join(process.cwd(), ".aal", "alive-patches");
  fs.mkdirSync(outDir, { recursive: true });
  const file = path.join(outDir, `promote_${plan.metric_id}_${Date.now()}.json`);
  fs.writeFileSync(file, JSON.stringify(patch, null, 2));
  return file;
}
