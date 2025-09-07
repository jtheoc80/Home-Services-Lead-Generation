import axios from "axios";
import type { Permit } from "../adapters/houstonXlsx";

export async function upsertPermits(perms: Permit[]) {
  if (!perms.length) return { upserted: 0 };

  const url = `${process.env.SUPABASE_URL}/rest/v1/permits`;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!key) {
    throw new Error("SUPABASE_SERVICE_ROLE_KEY environment variable is not set.");
  }
  const { headers } = await axios.post(url, perms, {
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      Prefer: "resolution=merge-duplicates",
      "Content-Type": "application/json",
    },
    params: { on_conflict: "source_system,permit_id" }
  });
  // content-range like "0-99/100"
  const cr = String(headers["content-range"] || "");
  const upserted = Number(cr.split("/")[1] || perms.length);
  return { upserted };
}