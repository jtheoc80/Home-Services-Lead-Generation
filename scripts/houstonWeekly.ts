
// Wrapper module for Houston weekly permit data fetching
export { fetchHoustonWeeklyXlsx as fetchHoustonWeekly } from "./adapters/houstonXlsx";

import axios from "axios";
import * as XLSX from "xlsx";
import type { Permit } from "./supabaseSink";

const normTrade = (v: string | undefined) => {
  const s = (v || "").toLowerCase();
  if (s.includes("elect")) return "Electrical";
  if (s.includes("plumb")) return "Plumbing";
  if (s.includes("mech")) return "Mechanical";
  return "General";
};

export async function fetchHoustonWeekly(url: string, days = 7): Promise<Permit[]> {
  const res = await axios.get<ArrayBuffer>(url, { responseType: "arraybuffer", timeout: 60000 });
  const wb = XLSX.read(res.data);
  const sheet = wb.Sheets[wb.SheetNames[0]];
  const rows: any[] = XLSX.utils.sheet_to_json(sheet, { defval: "" });

  const cutoff = new Date(Date.now() - days * 86400000);
  const getKey = (r: any, target: string) =>
    Object.keys(r).find(k => k.toLowerCase().replace(/\s+/g, "") === target);

  const out: Permit[] = [];
  for (const r of rows) {
    const idK = getKey(r, "permitnumber") ?? getKey(r, "permitid") ?? getKey(r, "permit_no");
    const dtK = getKey(r, "issuedate") ?? getKey(r, "issue_date") ?? getKey(r, "dateissued");
    if (!idK || !dtK) continue;
    const id = String(r[idK]).trim();
    const d = r[dtK] instanceof Date ? r[dtK] : new Date(r[dtK]);
    if (!id || Number.isNaN(+d) || d < cutoff) continue;

    const tradeK = getKey(r, "worktype") ?? getKey(r, "tradetype") ?? getKey(r, "trade");
    const addrK  = getKey(r, "address") ?? getKey(r, "projectaddress") ?? getKey(r, "siteaddress");
    const zipK   = getKey(r, "zip") ?? getKey(r, "zipcode") ?? getKey(r, "postalcode");
    const valK   = getKey(r, "valuation") ?? getKey(r, "jobvalue");
    const contrK = getKey(r, "contractor") ?? getKey(r, "company");

    out.push({
      source_system: "city_of_houston",
      permit_id: id,
      issue_date: new Date(d).toISOString(),
      trade: normTrade(tradeK ? r[tradeK] : undefined),
      address: addrK ? String(r[addrK]).trim() : undefined,
      zipcode: zipK ? String(r[zipK]).trim() : undefined,
      valuation: valK ? Number(String(r[valK]).replace(/[^\d.]/g, "")) || null : null,
      contractor: contrK ? String(r[contrK]).trim() : null,
    });
  }
  return out;
}
