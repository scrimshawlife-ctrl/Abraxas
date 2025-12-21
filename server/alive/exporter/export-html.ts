import { AliveRunResult } from "@shared/alive/schema";
import { exportAsMarkdown } from "./export-md";

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

export function exportAsHtml(run: AliveRunResult): string {
  const markdown = exportAsMarkdown(run);
  return [
    "<!doctype html>",
    "<html>",
    "<head>",
    "<meta charset=\"utf-8\" />",
    "<title>ALIVE Report</title>",
    "</head>",
    "<body>",
    `<pre>${escapeHtml(markdown)}</pre>`,
    "</body>",
    "</html>",
  ].join("\n");
}
