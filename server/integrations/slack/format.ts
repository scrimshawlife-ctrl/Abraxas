import { AliveRunResult } from "@shared/alive/schema";

export function formatSlackMessage(run: AliveRunResult): { text: string } {
  const alerts = run.view.alerts ?? [];
  const agg = run.signature.aggregates ?? {};

  const lines = [
    "*ALIVE Enterprise Alert*",
    `Run: \`${run.provenance.run_id}\``,
    `Influence: ${agg.influence_intensity?.value ?? "n/a"} | Vitality: ${agg.vitality_charge?.value ?? "n/a"} | Logistics: ${agg.logistics_friction?.value ?? "n/a"}`,
    "",
    alerts.length ? `*Alerts (${alerts.length})*` : "*Alerts:* none",
    ...alerts.slice(0, 8).map((alert) => `• [${alert.severity.toUpperCase()}] ${alert.code} — ${alert.message}`),
  ];

  return { text: lines.join("\n") };
}
