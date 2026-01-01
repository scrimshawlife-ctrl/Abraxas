import { AliveTier } from "./schema";

export type AliveExportFormat =
  | "json"
  | "csv"
  | "pdf"
  | "md"
  | "html"
  | "webhook"
  | "slack"
  | "email"
  | "bi_table";

export type AliveIntegration = "slack" | "email" | "webhook" | "teams" | "notion" | "jira";

export interface AliveExportCapability {
  tier: AliveTier;
  allowed_formats: AliveExportFormat[];
  allowed_integrations: AliveIntegration[];
  max_exports_per_day?: number;
  include_raw_metrics: boolean;
  include_components: boolean;
  include_strain_details: boolean;
}

export const ALIVE_EXPORT_CAPS: AliveExportCapability[] = [
  {
    tier: "psychonaut",
    allowed_formats: ["json", "md", "pdf"],
    allowed_integrations: [],
    max_exports_per_day: 10,
    include_raw_metrics: false,
    include_components: false,
    include_strain_details: false,
  },
  {
    tier: "academic",
    allowed_formats: ["json", "csv", "md", "pdf", "html", "bi_table"],
    allowed_integrations: ["webhook"],
    max_exports_per_day: 50,
    include_raw_metrics: true,
    include_components: false,
    include_strain_details: true,
  },
  {
    tier: "enterprise",
    allowed_formats: ["json", "csv", "pdf", "html", "bi_table", "webhook", "slack", "email"],
    allowed_integrations: ["slack", "email", "webhook", "teams", "notion", "jira"],
    max_exports_per_day: 500,
    include_raw_metrics: true,
    include_components: true,
    include_strain_details: true,
  },
];
