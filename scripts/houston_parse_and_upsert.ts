import fs from "node:fs";
import path from "node:path";
import * as XLSX from "xlsx";
import { createClient } from "@supabase/supabase-js";

const OUT_DIR = process.env.OUT_DIR || "artifacts/houston";
const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY!;

function mapRow(r: Record<string, any>) {
  // adjust column names to the Houston sheet headers
  const addr = r["Address"] || r["SITE_ADDR"] || r["ADDRESS"] || null;
  const zip  = (r["Zip"] || r["ZIP"] || r["ZIPCODE"] || "").toString().slice(0,5) || null;
  const issued = r["Issue Date"] || r["ISSUED_DATE"] || r["ISSUED"] || null;
  const permitNo = r["Permit #"] || r["PERMIT_NO"] || r["PERMIT"] || r["NUMBER"] || null;
  const trade = r["Trade"] || r["TRADE"] || r["Permit Type"] || null;

  return {
    source: "city_of_houston_xlsx",
    external_permit_id: String(permitNo ?? ""),
    issued_date: issued ? new Date(issued) : null,
    trade: trade ?? null,
    address: addr ?? null,
    zipcode: zip,
    county: "Harris",
    jurisdiction: "City of Houston",
    raw: r
  };
}

(async () => {
  const client = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, { auth: { persistSession: false }});

  const files = fs.readdirSync(OUT_DIR).filter(f => /\.xlsx?$/i.test(f));
  if (!files.length) throw new Error(`No XLS/XLSX in ${OUT_DIR}`);

  for (const f of files) {
    const wb = XLSX.readFile(path.join(OUT_DIR, f));
    const sheet = wb.Sheets[wb.SheetNames[0]];
    const rows: any[] = XLSX.utils.sheet_to_json(sheet, { defval: null });
    const mapped = rows.map(mapRow).filter(x => x.external_permit_id);

    if (mapped.length) {
      const { error } = await client.from("permits")
        .upsert(mapped, { onConflict: "source,external_permit_id" });
      if (error) throw error;
      console.log(`Upserted ${mapped.length} from ${f}`);
    }
  }

  // call your RPC to mint leads
  const { data, error } = await client.rpc("upsert_leads_from_permits_limit", { p_limit: 50, p_days: 365 });
  if (error) throw error;
  console.log(`Leads upserted this run: ${data}`);
})();