import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";

const WEEKLY_URL = process.env.HOUSTON_WEEKLY_URL!;
const SOLD_URL   = process.env.HOUSTON_SOLD_URL!;
const OUT_DIR    = process.env.OUT_DIR || "artifacts/houston";
const USER_AGENT = process.env.USER_AGENT || "LeadETL/1.0";

async function downloadFrom(pageUrl: string, matchRe: RegExp) {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ acceptDownloads: true, userAgent: USER_AGENT });
  const page = await ctx.newPage();

  await page.goto(pageUrl, { waitUntil: "domcontentloaded", timeout: 90000 });
  await page.waitForLoadState("networkidle", { timeout: 30000 });

  // links to spreadsheets
  const anchors = await page.$$("a[href$='.xls'], a[href$='.xlsx']");
  if (!anchors.length) {
    await browser.close();
    throw new Error(`No XLS/XLSX links found on ${pageUrl}`);
  }

  // prefer link whose text matches our intent
  let target = null as null | import("playwright").ElementHandle<HTMLElement>;
  for (const a of anchors) {
    const text = ((await a.innerText()) || "").trim();
    const href = await a.getAttribute("href");
    if (matchRe.test(text) || (href && matchRe.test(href))) {
      target = a; break;
    }
  }
  if (!target) target = anchors[0];

  const [download] = await Promise.all([
    page.waitForEvent("download", { timeout: 60000 }),
    target!.click()
  ]);

  await fs.mkdir(OUT_DIR, { recursive: true });
  const suggested = download.suggestedFilename();
  const dest = path.join(OUT_DIR, suggested);
  await download.saveAs(dest);
  await browser.close();
  console.log(`Saved: ${dest}`);
  return dest;
}

(async () => {
  const which = process.argv[2]; // "weekly" | "sold"
  if (!which || !["weekly", "sold"].includes(which)) {
    console.error("Usage: tsx scripts/houston_download.ts <weekly|sold>");
    process.exit(2);
  }
  const url = which === "weekly" ? WEEKLY_URL : SOLD_URL;
  const re  = which === "weekly" ? /weekly/i : /sold/i;
  await downloadFrom(url, re);
})();