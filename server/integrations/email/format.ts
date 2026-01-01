import { AliveRunResult } from "@shared/alive/schema";

export function formatAliveEmail(run: AliveRunResult): { subject: string; text: string } {
  const alerts = run.view.alerts ?? [];
  const agg = run.signature.aggregates ?? {};

  const subject = `ALIVE: ${alerts.length ? `${alerts.length} alert(s)` : "No alerts"} — run ${run.provenance.run_id.slice(0, 8)}`;

  const text = [
    "ALIVE ENTERPRISE REPORT",
    `Run: ${run.provenance.run_id}`,
    `Created: ${run.provenance.created_at}`,
    "",
    "Aggregates:",
    `- Influence: ${agg.influence_intensity?.value ?? "n/a"} (conf ${agg.influence_intensity?.confidence ?? "n/a"})`,
    `- Vitality: ${agg.vitality_charge?.value ?? "n/a"} (conf ${agg.vitality_charge?.confidence ?? "n/a"})`,
    `- Logistics: ${agg.logistics_friction?.value ?? "n/a"} (conf ${agg.logistics_friction?.confidence ?? "n/a"})`,
    "",
    "Alerts:",
    ...(alerts.length
      ? alerts.map((alert) => `- [${alert.severity.toUpperCase()}] ${alert.code}: ${alert.message}`)
      : ["- none"]),
  ].join("\n");

  return { subject, text };
}
