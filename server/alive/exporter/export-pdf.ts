import type { AliveMetricValue, AliveRunResult } from "@shared/alive/schema";

const PAGE_WIDTH = 612;
const PAGE_HEIGHT = 792;
const MARGIN = 50;
const LINE_HEIGHT = 14;

export function exportAsPdf(run: AliveRunResult): { mime: string; encoding: string; data: string } {
  const lines = buildLines(run);
  const pdfBytes = renderPdf(lines);
  return {
    mime: "application/pdf",
    encoding: "base64",
    data: Buffer.from(pdfBytes).toString("base64"),
  };
}

function buildLines(run: AliveRunResult): string[] {
  const signature = run.signature || { influence: [], vitality: [], life_logistics: [] };
  const lines: string[] = [
    "ALIVE Run Export",
    `Run ID: ${run.provenance?.run_id ?? "unknown"}`,
    `Tier: ${run.view?.tier ?? "unknown"}`,
    `Schema: ${run.provenance?.schema_version ?? "unknown"}`,
    `Engine: ${run.provenance?.engine_version ?? "unknown"}`,
    "",
    "Influence Metrics:",
  ];

  appendMetrics(lines, signature.influence);
  lines.push("", "Vitality Metrics:");
  appendMetrics(lines, signature.vitality);
  lines.push("", "Life-Logistics Metrics:");
  appendMetrics(lines, signature.life_logistics);

  return lines;
}

function appendMetrics(lines: string[], metrics: AliveMetricValue[] = []) {
  if (!metrics.length) {
    lines.push("  (none)");
    return;
  }

  for (const metric of metrics) {
    lines.push(
      `  - ${metric.metric_id} v${metric.version} [${metric.status}] value=${metric.value}` +
        ` confidence=${metric.confidence}`
    );
  }
}

function renderPdf(lines: string[]): Uint8Array {
  const linesPerPage = Math.max(1, Math.floor((PAGE_HEIGHT - 2 * MARGIN) / LINE_HEIGHT));
  const pages: string[][] = [];
  for (let i = 0; i < lines.length; i += linesPerPage) {
    pages.push(lines.slice(i, i + linesPerPage));
  }

  const pageObjects: string[] = [];
  const pagesKids: string[] = [];

  pages.forEach((pageLines, pageIndex) => {
    const pageObjNum = 4 + pageIndex * 2;
    const contentObjNum = pageObjNum + 1;
    pagesKids.push(`${pageObjNum} 0 R`);

    const textLines: string[] = ["BT", "/F1 11 Tf"];
    let y = PAGE_HEIGHT - MARGIN;
    for (const line of pageLines) {
      const escaped = escapePdfText(String(line));
      textLines.push(`1 0 0 1 ${MARGIN} ${y} Tm (${escaped}) Tj`);
      y -= LINE_HEIGHT;
    }
    textLines.push("ET");
    const content = textLines.join("\n");
    const contentBytes = Buffer.from(content, "latin1");
    const contentObj = `<< /Length ${contentBytes.length} >>\nstream\n${content}\nendstream`;
    const pageObj =
      `<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 3 0 R >> >> ` +
      `/MediaBox [0 0 ${PAGE_WIDTH} ${PAGE_HEIGHT}] /Contents ${contentObjNum} 0 R >>`;

    pageObjects.push(pageObj, contentObj);
  });

  const catalogObj = "<< /Type /Catalog /Pages 2 0 R >>";
  const pagesObj = `<< /Type /Pages /Kids [ ${pagesKids.join(" ")} ] /Count ${pagesKids.length} >>`;
  const fontObj = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>";
  const objects = [catalogObj, pagesObj, fontObj, ...pageObjects];

  const header = Buffer.from("%PDF-1.4\n%\xE2\xE3\xCF\xD3\n", "latin1");
  const parts: Buffer[] = [header];
  const offsets: number[] = [0];
  let cursor = header.length;

  objects.forEach((obj, idx) => {
    const entry = `${idx + 1} 0 obj\n${obj}\nendobj\n`;
    const buffer = Buffer.from(entry, "latin1");
    offsets.push(cursor);
    parts.push(buffer);
    cursor += buffer.length;
  });

  const xrefStart = cursor;
  const xrefLines = ["xref", `0 ${objects.length + 1}`, "0000000000 65535 f "];
  for (const offset of offsets.slice(1)) {
    xrefLines.push(`${String(offset).padStart(10, "0")} 00000 n `);
  }
  const xref = Buffer.from(xrefLines.join("\n"), "latin1");
  const trailer = Buffer.from(
    `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefStart}\n%%EOF\n`,
    "latin1"
  );

  parts.push(xref, trailer);
  return Buffer.concat(parts);
}

function escapePdfText(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
}
