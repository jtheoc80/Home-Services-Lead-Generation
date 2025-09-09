// scripts/houston_download.ts
import { chromium } from "playwright";
import * as fs from "fs/promises";
import * as path from "path";

const WEEKLY_URL = process.env.HOUSTON_WEEKLY_URL!;
const SOLD_URL   = process.env.HOUSTON_SOLD_URL!;
const OUT_DIR    = process.env.OUT_DIR || "artifacts/houston";

async function downloadFrom(pageUrl: string, containsText: RegExp) {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ acceptDownloads: true, userAgent: process.env.USER_AGENT || "LeadETL/1.0" });
  const page = await ctx.newPage();
  await page.goto(pageUrl, { waitUntil: "domcontentloaded", timeout: 60000 });

  // find all XLS/XLSX links; prefer ones whose text matches our filter
  const anchors = await page.$$("a[href$='.xls'], a[href$='.xlsx']");
  if (!anchors.length) throw new Error(`No XLS/XLSX links found on ${pageUrl}`);

  // choose matching link if available, else first xlsx
  let link = null;
  for (const a of anchors) {
    const text = ((await a.innerText()) || "").trim();
    if (containsText.test(text)) { link = a; break; }
  }
  if (!link) link = anchors[0];
  if (!link) throw new Error(`No matching XLS/XLSX link found on ${pageUrl}`);

  const [download] = await Promise.all([
    link.click(),
    page.waitForEvent("download", { timeout: 60000 })
  ]);
  await fs.mkdir(OUT_DIR, { recursive: true });
  const suggested = download.suggestedFilename();
  const dest = path.join(OUT_DIR, suggested);
  await download.saveAs(dest);
  await browser.close();
  return dest;
}

(async () => {
  const which = process.argv[2]; // weekly|sold
  if (!which) throw new Error("Usage: tsx scripts/houston_download.ts <weekly|sold>");
  const url = which === "weekly" ? WEEKLY_URL : SOLD_URL;
  const regex = which === "weekly" ? /weekly/i : /sold/i;
  const file = await downloadFrom(url, regex);
  console.log(`Saved: ${file}`);
})();