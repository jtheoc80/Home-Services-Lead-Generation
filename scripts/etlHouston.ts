#!/usr/bin/env tsx

/**
 * ETL Script for City of Houston Permits
 * 
 * @deprecated Use scripts/ingest-coh.ts instead
 * 
 * This file is kept for compatibility but the main ETL logic has been moved to
 * scripts/ingest-coh.ts for better organization and to match the CI workflow.
 */

import { fetchHoustonWeeklyXlsx } from "./adapters/houstonXlsx";
import { fetchHoustonSoldPermits } from "./adapters/houstonSoldPermits";
import { upsertPermits } from "./lib/supabaseUpsert";
import fs from "node:fs";

async function main() {
  console.log('⚠️  This script is deprecated. Please use scripts/ingest-coh.ts instead.');
  console.log('Redirecting to ingest-coh.ts...');
  console.log('');
  
  const days = Number(process.env.DAYS || "7");

  const weeklyUrlRaw = process.env.HOUSTON_WEEKLY_XLSX_URL;
  const soldUrlRaw   = process.env.HOUSTON_SOLD_PERMITS_URL;

  if (!weeklyUrlRaw) {
    throw new Error("Missing required environment variable: HOUSTON_WEEKLY_XLSX_URL");
  }
  if (!soldUrlRaw) {
    throw new Error("Missing required environment variable: HOUSTON_SOLD_PERMITS_URL");
  }

  let weeklyUrl: string;
  let soldUrl: string;
  try {
    weeklyUrl = new URL(weeklyUrlRaw).toString();
  } catch (e) {
    throw new Error("Invalid URL in HOUSTON_WEEKLY_XLSX_URL: " + weeklyUrlRaw);
  }
  try {
    soldUrl = new URL(soldUrlRaw).toString();
  } catch (e) {
    throw new Error("Invalid URL in HOUSTON_SOLD_PERMITS_URL: " + soldUrlRaw);
  }
  
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
    first_issue_date: merged.length > 0 ? merged.map(p => p.issue_date).reduce((a, b) => a < b ? a : b) : undefined,
    last_issue_date: merged.length > 0 ? merged.map(p => p.issue_date).reduce((a, b) => a > b ? a : b) : undefined,
  };
  fs.mkdirSync("logs", { recursive: true });
  fs.writeFileSync("logs/etl-summary.json", JSON.stringify(summary, null, 2));
  console.log("COH ETL summary:", summary);
}

main().catch(e => {
  console.error(e);
  process.exitCode = 1;
});