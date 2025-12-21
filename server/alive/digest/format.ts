import type { AliveDigest } from "@shared/alive/digest";

export function formatDigestSlack(digest: AliveDigest): { text: string } {
  const alerts = digest.alerts ?? [];
  const anomalies = digest.anomalies ?? [];

  const lines = [
    `*ALIVE Digest (${digest.window})*`,
    `Risk: *${digest.headline.risk_level.toUpperCase()}*`,
    digest.headline.summary,
    "",
    alerts.length ? `*Alerts (${alerts.length})*` : "*Alerts:* none",
    ...alerts.slice(0, 5).map((alert) => `• [${alert.severity.toUpperCase()}] ${alert.code}`),
    "",
    anomalies.length ? `*Anomalies (${anomalies.length})*` : "*Anomalies:* none",
    ...anomalies.slice(0, 3).map((anomaly) => `• [${anomaly.severity.toUpperCase()}] ${anomaly.code}`),
  ];

  return { text: lines.join("\n") };
}

export function formatDigestEmail(digest: AliveDigest): { subject: string; text: string } {
  const alerts = digest.alerts ?? [];
  const anomalies = digest.anomalies ?? [];

  const subject = `ALIVE Digest (${digest.window}) — ${digest.headline.risk_level.toUpperCase()} risk`;

  const text = [
    "ALIVE ENTERPRISE DIGEST",
    `Window: ${digest.window}`,
    `Generated: ${digest.generated_at}`,
    "",
    `Risk Level: ${digest.headline.risk_level.toUpperCase()}`,
    digest.headline.summary,
    "",
    "Alerts:",
    ...(alerts.length
      ? alerts.map((alert) => `- [${alert.severity.toUpperCase()}] ${alert.code}: ${alert.message}`)
      : ["- none"]),
    "",
    "Anomalies:",
    ...(anomalies.length
      ? anomalies.map((anomaly) => `- [${anomaly.severity.toUpperCase()}] ${anomaly.code}: ${anomaly.description}`)
      : ["- none"]),
  ].join("\n");

  return { subject, text };
}
