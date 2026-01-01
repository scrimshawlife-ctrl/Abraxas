import { AliveRunResult } from "@shared/alive/schema";
import { exportAsBITable, type AliveBIRow } from "./export-bi-table";

const CSV_COLUMNS: Array<keyof AliveBIRow> = [
  "run_id",
  "created_at",
  "tier",
  "metric_id",
  "axis",
  "value",
  "confidence",
  "status",
  "version",
];

function escapeCsv(value: string | number): string {
  const raw = String(value ?? "");
  if (raw.includes(",") || raw.includes("\n") || raw.includes("\"")) {
    return `"${raw.replace(/\"/g, '""')}"`;
  }
  return raw;
}

export function exportAsCsv(run: AliveRunResult): string {
  const rows = exportAsBITable(run);
  const header = CSV_COLUMNS.join(",");
  const lines = rows.map((row) =>
    CSV_COLUMNS.map((col) => escapeCsv(row[col])).join(",")
  );
  return [header, ...lines].join("\n");
}
