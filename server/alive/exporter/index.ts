import { AliveRunResult } from "@shared/alive/schema";
import type { AliveExportFormat } from "@shared/alive/exports";
import { exportAsBITable } from "./export-bi-table";
import { exportAsCsv } from "./export-csv";
import { exportAsHtml } from "./export-html";
import { exportAsJson } from "./export-json";
import { exportAsMarkdown } from "./export-md";

export function exportAliveRun(run: AliveRunResult, format: AliveExportFormat): string | object {
  switch (format) {
    case "json":
      return exportAsJson(run);
    case "md":
      return exportAsMarkdown(run);
    case "html":
      return exportAsHtml(run);
    case "csv":
      return exportAsCsv(run);
    case "bi_table":
      return exportAsBITable(run);
    default:
      throw new Error(`Unsupported export format: ${format}`);
  }
}
