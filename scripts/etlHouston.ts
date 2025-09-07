import { fetchHoustonWeeklyXlsx } from "./adapters/houstonXlsx";
import { fetchHoustonSoldPermits } from "./adapters/houstonSoldPermits";
import { upsertPermits } from "./lib/supabaseUpsert";
import fs from "node:fs";

async function main() {
  const days = Number(process.env.DAYS || "7");
  const weeklyUrl = process.env.HOUSTON_WEEKLY_XLSX_URL!;
  const soldUrl   = process.env.HOUSTON_SOLD_PERMITS_URL!;

  const weekly = await fetchHoustonWeeklyXlsx(weeklyUrl, days);
  const sold   = await fetchHoustonSoldPermits(soldUrl, Math.min(days, 2));

  // de-dupe on (source_system, permit_id, issue_date)
  const seen = new Set<string>();
  const merged = [...weekly, ...sold].filter(p => {
    const k = `${p.source_system}|${p.permit_id}|${p.issue_date.slice(0,10)}`;
    if (seen.has(k)) return false;
    seen.add(k); return true;
  });

  const { upserted } = await upsertPermits(merged);

  // write summary for CI
  const summary = {
    source: "city_of_houston",
    fetched_weekly: weekly.length,
    fetched_sold: sold.length,
    merged: merged.length,
    upserted,
    first_issue_date: merged.reduce((m,p)=> m && m < p.issue_date ? m : p.issue_date, merged[0]?.issue_date),
    last_issue_date: merged.reduce((m,p)=> m && m > p.issue_date ? m : p.issue_date, merged[0]?.issue_date),
  };
  fs.mkdirSync("logs", { recursive: true });
  fs.writeFileSync("logs/etl-summary.json", JSON.stringify(summary, null, 2));
  console.log("COH ETL summary:", summary);
}
main().catch(e => {
  console.error(e);
  process.exitCode = 1;
});