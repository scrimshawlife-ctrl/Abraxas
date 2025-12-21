import fs from "fs";
import { ProposalStore } from "./storage";
import { computeScores, blockersFor } from "./evaluate";
import { writePromotionPatch } from "./promote";

async function main(store: ProposalStore) {
  const [cmd, arg] = process.argv.slice(2);

  if (cmd === "list") {
    const statusIndex = process.argv.indexOf("--status");
    const status = statusIndex >= 0 ? process.argv[statusIndex + 1] : undefined;
    const items = await store.list(status as any);
    for (const record of items) {
      console.log(
        `${record.status}\t${record.proposal.proposed_metric_id}\t${record.proposal.working_name}\t${record.proposal_id}`
      );
    }
    return;
  }

  if (cmd === "evaluate") {
    if (!arg) throw new Error("proposal_id required");
    const seriesIndex = process.argv.indexOf("--series");
    if (seriesIndex < 0) {
      throw new Error("metric series JSON required via --series <path>");
    }
    const seriesPath = process.argv[seriesIndex + 1];
    if (!seriesPath) throw new Error("metric series JSON required via --series <path>");

    const record = await store.get(arg);
    if (!record) throw new Error("proposal not found");

    const seriesRaw = fs.readFileSync(seriesPath, "utf-8");
    const metricSeries = JSON.parse(seriesRaw);

    const scores = computeScores({
      metric_series: metricSeries,
      golden_fp: 0,
      golden_fn: 0,
    });
    const blockers = blockersFor(scores, metricSeries.length);
    console.log(
      JSON.stringify(
        {
          proposal_id: record.proposal_id,
          scores,
          blockers,
        },
        null,
        2
      )
    );
    return;
  }

  if (cmd === "promote") {
    if (!arg) throw new Error("proposal_id required");
    const record = await store.get(arg);
    if (!record) throw new Error("proposal not found");

    if (!record.eval || (record.eval.blockers && record.eval.blockers.length)) {
      throw new Error(
        `cannot promote; blockers: ${(record.eval?.blockers ?? []).join(",")}`
      );
    }

    const patchFile = writePromotionPatch({
      metric_id: record.proposal.proposed_metric_id,
      new_status: "promoted",
      new_version: "1.0.0",
      notes: record.notes,
    });

    record.status = "ready_to_promote";
    record.notes = [...(record.notes ?? []), `promotion_patch:${patchFile}`];
    await store.upsert(record);

    console.log(`Wrote promotion patch: ${patchFile}`);
    return;
  }

  console.log(
    "Usage: alive-metrics list|evaluate|approve|promote|reject <proposal_id>"
  );
}

export { main };
