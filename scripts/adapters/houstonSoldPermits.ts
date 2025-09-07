import axios from "axios";
import * as cheerio from "cheerio";
import { Permit } from "./houstonXlsx";
import { normTrade } from "./houstonUtils";
export async function fetchHoustonSoldPermits(listUrl: string, sinceDays = 2): Promise<Permit[]> {
  // NOTE: adjust to the site's query params if available (date filters).
  const html = await axios.get(listUrl, { timeout: 30_000 }).then(r => r.data);
  const $ = cheerio.load(html);

  const cutoff = new Date(Date.now() - sinceDays*24*60*60*1000);
  const out: Permit[] = [];

  // Generic table extraction; adapt selectors to the actual markup
  $("table tbody tr").each((_, tr) => {
    const tds = $(tr).find("td");
    if (tds.length < 4) return;

    const permit_id = $(tds[0]).text().trim();
    const issueRaw  = $(tds[1]).text().trim();
    const tradeRaw  = $(tds[2]).text().trim();
    const addr      = $(tds[3]).text().trim();

    const d = new Date(issueRaw);
    if (!permit_id || isNaN(+d) || d < cutoff) return;

    out.push({
      source_system: "city_of_houston",
      permit_id,
      issue_date: d.toISOString(),
      trade: normTrade(tradeRaw),
      address: addr || undefined,
      raw: { permit_id, issueRaw, tradeRaw, addr }
    });
  });

  return out;
}