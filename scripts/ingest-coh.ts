import { fetchHoustonWeekly } from "./houstonWeekly";
import { upsertPermits } from "./supabaseSink";
import fs from "node:fs";

async function main() {
  const weeklyUrl = process.env.HOUSTON_WEEKLY_XLSX_URL!;
  const days = Number(process.env.DAYS || "7");

  console.log("⏬ Fetching Houston weekly:", weeklyUrl);
  const rows = await fetchHoustonWeekly(weeklyUrl, days);
  console.log("📦 Parsed rows:", rows.length);

  const up = await upsertPermits(rows, 500);
  console.log("⬆️  Upserted rows:", up);

  // write a small summary for CI
  fs.mkdirSync("logs", { recursive: true });
  fs.writeFileSync("logs/etl-summary.json", JSON.stringify({
    source: "city_of_houston",
    parsed: rows.length,
    upserted: up,
  }, null, 2));
}
main().catch(e => { console.error(e); process.exit(1); });