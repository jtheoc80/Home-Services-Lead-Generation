import axios from "axios";
import type { Permit } from "../adapters/houstonXlsx";

// Backward compatible overload - returns object
export async function upsertPermits(perms: Permit[]): Promise<{ upserted: number }>;
// New overload with batch size - returns number directly  
export async function upsertPermits(perms: Permit[], batchSize: number): Promise<number>;
// Implementation
export async function upsertPermits(perms: Permit[], batchSize?: number): Promise<{ upserted: number } | number> {
  if (!perms.length) {
    return batchSize !== undefined ? 0 : { upserted: 0 };
  }

  const url = `${process.env.SUPABASE_URL}/rest/v1/permits`;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!key) {
    throw new Error("SUPABASE_SERVICE_ROLE_KEY environment variable is not set.");
  }

  const effectiveBatchSize = batchSize || 500;
  let totalUpserted = 0;

  // Process in batches
  for (let i = 0; i < perms.length; i += effectiveBatchSize) {
    const batch = perms.slice(i, i + effectiveBatchSize);
    
    const { headers } = await axios.post(url, batch, {
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
    const batchUpserted = Number(cr.split("/")[1] || batch.length);
    totalUpserted += batchUpserted;
  }

  // Return different types based on whether batchSize was provided
  return batchSize !== undefined ? totalUpserted : { upserted: totalUpserted };
}