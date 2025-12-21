import { ALIVE_EXPORT_CAPS } from "@shared/alive/exports";
import type { AliveTier } from "@shared/alive/schema";
import type { AliveExportFormat, AliveIntegration } from "@shared/alive/exports";

export function assertAllowed(
  tier: AliveTier,
  format?: AliveExportFormat,
  integration?: AliveIntegration
): void {
  const caps = ALIVE_EXPORT_CAPS.find((cap) => cap.tier === tier);
  if (!caps) {
    throw new Error("Unknown tier");
  }

  if (format && !caps.allowed_formats.includes(format)) {
    throw new Error(`Format not allowed for tier: ${tier}`);
  }

  if (integration && !caps.allowed_integrations.includes(integration)) {
    throw new Error(`Integration not allowed for tier: ${tier}`);
  }
}
