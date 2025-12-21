import { AliveRunResult } from "@shared/alive/schema";

function getMetric(run: AliveRunResult, id: string): number {
  for (const axis of ["influence", "vitality", "life_logistics"] as const) {
    for (const metric of run.signature[axis] ?? []) {
      if (metric.metric_id === id) {
        return metric.value;
      }
    }
  }
  return 0;
}

export function computeEnterpriseAlerts(
  run: AliveRunResult
): NonNullable<AliveRunResult["view"]["alerts"]> {
  const ncr = getMetric(run, "IM.NCR");
  const rcf = getMetric(run, "IM.RCF");
  const rfc = getMetric(run, "IM.RFC");
  const gi = getMetric(run, "VM.GI");
  const lfc = getMetric(run, "LL.LFC");

  const alerts: NonNullable<AliveRunResult["view"]["alerts"]> = [];

  if (rcf >= 0.6 && ncr >= 0.6 && rfc <= 0.35) {
    alerts.push({
      code: "ALIVE.LOOP.SELFSEAL",
      severity: "critical",
      message:
        "High loop + high compression + low reality friction: high capture velocity, low correctability.",
      recommended_next: [
        "Require falsifiable hooks",
        "Add disconfirming pathways",
        "Limit sloganization in comms",
      ],
    });
  }

  if (ncr >= 0.65 && gi >= 0.65) {
    alerts.push({
      code: "ALIVE.IGNITION.CREATIVE",
      severity: "warning",
      message:
        "High compression + high generativity: creative ignition—novelty may be channeling into a single frame.",
      recommended_next: [
        "Increase causal plurality",
        "Encourage competing interpretations",
        "Monitor for channel-lock",
      ],
    });
  }

  if (lfc >= 0.7 && gi <= 0.3) {
    alerts.push({
      code: "ALIVE.BURNOUT.ZOMBIE",
      severity: "notice",
      message: "High life-demand with low novelty: burnout/brittleness risk.",
      recommended_next: [
        "Reduce operational load",
        "Add renewal cycles",
        "Simplify rituals/processes",
      ],
    });
  }

  if (rfc >= 0.7 && gi >= 0.6) {
    alerts.push({
      code: "ALIVE.LEARNING.HIGH",
      severity: "notice",
      message: "High testability + high generativity: supports resilient learning loops.",
      recommended_next: [
        "Run small experiments",
        "Instrument metrics",
        "Publish disconfirming results",
      ],
    });
  }

  return alerts;
}
