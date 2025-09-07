import axios from "axios";
import * as cheerio from "cheerio";
import { fetchHoustonWeeklyXlsx as fetchHoustonWeekly, type Permit } from "./adapters/houstonXlsx";
import { upsertPermits } from "./lib/supabaseUpsert";

const ARCHIVE = process.env.HOUSTON_WEEKLY_ARCHIVE_URL || "https://www.houstontx.gov/planning/DevelopRegs/dev_reports.html";
const WEEKS = Number(process.env.ARCHIVE_WEEKS || "12");

async function listWeeklyXlsx(n: number): Promise<string[]> {
  const html = (await axios.get(ARCHIVE, { timeout: 60000 })).data;
  const $ = cheerio.load(html);
  const links = new Set<string>();
  $("a[href$='.xlsx']").each((_, a) => {
    links.add(new URL($(a).attr("href")!, ARCHIVE).toString());
  });
  return Array.from(links).slice(0, n);
}

async function main() {
  const urls = await listWeeklyXlsx(WEEKS);
  let all: Permit[] = [];
  for (const url of urls) {
    const rows = await fetchHoustonWeekly(url, 365);
    all = all.concat(rows);
  }
  // simple de-dupe by (source_system, permit_id)
  const seen = new Set<string>();
  const dedup = all.filter(r => {
    const k = `${r.source_system}::${r.permit_id}`;
    if (seen.has(k)) return false;
    seen.add(k); return true;
  });
  console.log(`Parsed ${all.length} rows; deduped to ${dedup.length}`);
  const up = await upsertPermits(dedup, 500);
  console.log(`Upserted ${up} permits`);
}
main().catch(e => { console.error(e); process.exit(1); });