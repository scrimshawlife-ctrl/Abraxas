import { AliveRunResult } from "@shared/alive/schema";

export function exportAsMarkdown(run: AliveRunResult): string {
  const tier = run.view?.tier ?? "unknown";
  const agg = run.signature?.aggregates ?? {};
  const alerts = run.view?.alerts ?? [];
  const strainCount = run.strain?.signals?.length ?? 0;

  return [
    `# ALIVE Report (${tier})`,
    ``,
    `**Run:** ${run.provenance.run_id}`,
    `**Created:** ${run.provenance.created_at}`,
    ``,
    `## Aggregates`,
    `- Influence Intensity: ${agg.influence_intensity?.value ?? "n/a"} (conf ${agg.influence_intensity?.confidence ?? "n/a"})`,
    `- Vitality Charge: ${agg.vitality_charge?.value ?? "n/a"} (conf ${agg.vitality_charge?.confidence ?? "n/a"})`,
    `- Logistics Friction: ${agg.logistics_friction?.value ?? "n/a"} (conf ${agg.logistics_friction?.confidence ?? "n/a"})`,
    ``,
    `## Psychonaut Translation`,
    run.view?.translated
      ? [
          `- Pressure: ${run.view.translated.pressure}`,
          `- Pull: ${run.view.translated.pull}`,
          `- Agency Δ: ${run.view.translated.agency_delta}`,
          `- Drift Risk: ${run.view.translated.drift_risk}`,
        ].join("\n")
      : `- (not included)`,
    ``,
    `## Alerts (${alerts.length})`,
    ...alerts.map((alert) => `- **${alert.severity.toUpperCase()}** ${alert.code}: ${alert.message}`),
    ``,
    `## Strain`,
    `- signals: ${strainCount}`,
  ].join("\n");
}
