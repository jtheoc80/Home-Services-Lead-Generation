import axios from "axios";
import * as XLSX from "xlsx";

export type Permit = {
  source_system: "city_of_houston";
  permit_id: string;
  issue_date: string;  // ISO
  trade: string;
  address?: string;
  zipcode?: string;
  valuation?: number | null;
  contractor?: string | null;
  raw?: any;
};

const key = (o: any, name: string) =>
  Object.keys(o).find(k => k.toLowerCase().replace(/\s+/g, "") === name);

const normTrade = (v: string | undefined) => {
  const s = (v || "").toLowerCase();
  if (s.includes("elect")) return "Electrical";
  if (s.includes("plumb")) return "Plumbing";
  if (s.includes("mech")) return "Mechanical";
  return "General";
};

export async function fetchHoustonWeeklyXlsx(url: string, sinceDays = 7): Promise<Permit[]> {
  const res = await axios.get<ArrayBuffer>(url, { responseType: "arraybuffer", timeout: 60_000 });
  const wb = XLSX.read(res.data);
  const sheetName = wb.SheetNames[0];
  const rows: any[] = XLSX.utils.sheet_to_json(wb.Sheets[sheetName], { defval: "" });

  const cutoff = new Date(Date.now() - sinceDays*24*60*60*1000);
  const out: Permit[] = [];

  for (const r of rows) {
    const idKey = key(r, "permitnumber") ?? key(r, "permitid") ?? key(r, "permit_no");
    const dateKey = key(r, "issuedate") ?? key(r, "issue_date") ?? key(r, "dateissued");
    if (!idKey || !dateKey) continue;

    const permit_id = String(r[idKey]).trim();
    const dateVal = r[dateKey] instanceof Date ? r[dateKey] : new Date(r[dateKey]);
    if (!permit_id || isNaN(+dateVal)) continue;

    if (dateVal < cutoff) continue;

    const tradeKey = key(r, "worktype") ?? key(r, "tradetype") ?? key(r, "trade");
    const addrKey  = key(r, "address") ?? key(r, "projectaddress") ?? key(r, "siteaddress");
    const zipKey   = key(r, "zip") ?? key(r, "zipcode") ?? key(r, "postalcode");
    const valKey   = key(r, "valuation") ?? key(r, "jobvalue");
    const contrKey = key(r, "contractor") ?? key(r, "company");

    out.push({
      source_system: "city_of_houston",
      permit_id,
      issue_date: new Date(dateVal).toISOString(),
      trade: normTrade(r[tradeKey]),
      address: addrKey ? String(r[addrKey]).trim() : undefined,
      zipcode: zipKey ? String(r[zipKey]).trim() : undefined,
      valuation: valKey ? Number(String(r[valKey]).replace(/[^\d.]/g, "")) || null : null,
      contractor: contrKey ? String(r[contrKey]).trim() : null,
      raw: r,
    });
  }
  return out;
}