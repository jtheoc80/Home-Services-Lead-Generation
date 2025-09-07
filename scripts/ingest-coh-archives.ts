#!/usr/bin/env tsx

/**
 * Houston Archive Ingestion Script (scripts/ingest-coh-archives.ts)
 * 
 * Minimal ingest for multiple weeks of Houston permit data from archive.
 * This is a "drop-in script" that scrapes the Houston archive page for XLSX files,
 * fetches multiple weeks of permit data, deduplicates, and upserts to Supabase.
 * 
 * Environment Variables:
 *   HOUSTON_WEEKLY_ARCHIVE_URL - Archive page URL (default: Houston city archive)
 *   ARCHIVE_WEEKS - Number of weeks to fetch (default: 12)
 *   SUPABASE_URL - Supabase project URL (required)
 *   SUPABASE_SERVICE_ROLE_KEY - Supabase service role key (required)
 * 
 * Usage:
 *   export SUPABASE_URL=...
 *   export SUPABASE_SERVICE_ROLE_KEY=...
 *   export ARCHIVE_WEEKS=12
 *   npx tsx scripts/ingest-coh-archives.ts
 */

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