
#!/usr/bin/env tsx

/**
 * Houston Weekly Permits Adapter
 * 
 * Fetches and processes weekly permit data from Houston XLSX sources.
 * Based on existing scripts/adapters/houstonXlsx.ts but simplified for the new ETL flow.
 */

import axios from 'axios';
import * as XLSX from 'xlsx';

export interface HoustonPermit {
  source_system: 'city_of_houston';
  permit_id: string;
  issue_date: string; // ISO date string
  trade: string;
  address?: string;
  zipcode?: string;
  valuation?: number | null;
  contractor?: string | null;
  raw?: any;
}

/**
 * Find a key in an object case-insensitively and ignoring spaces
 */
const findKey = (obj: any, searchName: string): string | undefined => {
  return Object.keys(obj).find(k => 
    k.toLowerCase().replace(/\s+/g, '') === searchName.toLowerCase().replace(/\s+/g, '')
  );
};

/**
 * Normalize trade type from raw input
 */
const normalizeTrade = (value: string | undefined): string => {
  const s = (value || '').toLowerCase();
  if (s.includes('elect')) return 'Electrical';
  if (s.includes('plumb')) return 'Plumbing';
  if (s.includes('mech')) return 'Mechanical';
  if (s.includes('hvac')) return 'HVAC';
  if (s.includes('build')) return 'Building';
  return 'General';
};

/**
 * Parse valuation from string or number
 */
const parseValuation = (value: any): number | null => {
  if (typeof value === 'number') return value;
  if (typeof value === 'string') {
    // Remove currency symbols and commas
    const cleaned = value.replace(/[$,]/g, '');
    const parsed = parseFloat(cleaned);
    return isNaN(parsed) ? null : parsed;
  }
  return null;
};

/**
 * Fetch and parse Houston weekly permits from XLSX URL
 * 
 * @param url - URL to the Houston weekly permits XLSX file
 * @param sinceDays - Number of days to look back for permits (default: 7)
 * @returns Array of normalized permit records
 */
export async function fetchHoustonWeeklyPermits(url: string, sinceDays: number = 7): Promise<HoustonPermit[]> {
  console.log(`Fetching Houston weekly permits from: ${url}`);
  console.log(`Looking back ${sinceDays} days`);

  try {
    // Download XLSX file
    const response = await axios.get<ArrayBuffer>(url, { 
      responseType: 'arraybuffer', 
      timeout: 60_000 // 60 second timeout
    });

    console.log(`Downloaded ${response.data.byteLength} bytes`);

    // Parse XLSX
    const workbook = XLSX.read(response.data);
    const sheetName = workbook.SheetNames[0];
    const rows: any[] = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName], { defval: '' });

    console.log(`Parsed ${rows.length} rows from sheet: ${sheetName}`);

    // Calculate cutoff date
    const cutoffDate = new Date(Date.now() - sinceDays * 24 * 60 * 60 * 1000);
    console.log(`Cutoff date: ${cutoffDate.toISOString()}`);

    const permits: HoustonPermit[] = [];

    for (const row of rows) {
      try {
        // Find key columns (flexible naming)
        const permitIdKey = findKey(row, 'permitnumber') ?? findKey(row, 'permitid') ?? findKey(row, 'permit_no');
        const dateKey = findKey(row, 'issuedate') ?? findKey(row, 'issue_date') ?? findKey(row, 'dateissued');
        
        if (!permitIdKey || !dateKey) {
          continue; // Skip rows without required fields
        }

        const permitId = String(row[permitIdKey]).trim();
        const dateValue = row[dateKey] instanceof Date ? row[dateKey] : new Date(row[dateKey]);
        
        if (!permitId || isNaN(dateValue.getTime())) {
          continue; // Skip invalid permits
        }

        // Filter by date
        if (dateValue < cutoffDate) {
          continue;
        }

        // Extract other fields
        const tradeKey = findKey(row, 'worktype') ?? findKey(row, 'tradetype') ?? findKey(row, 'trade');
        const addressKey = findKey(row, 'address') ?? findKey(row, 'projectaddress') ?? findKey(row, 'siteaddress');
        const zipKey = findKey(row, 'zip') ?? findKey(row, 'zipcode') ?? findKey(row, 'postalcode');
        const valuationKey = findKey(row, 'valuation') ?? findKey(row, 'jobvalue') ?? findKey(row, 'value');
        const contractorKey = findKey(row, 'contractor') ?? findKey(row, 'contractorname') ?? findKey(row, 'builder');

        const permit: HoustonPermit = {
          source_system: 'city_of_houston',
          permit_id: permitId,
          issue_date: dateValue.toISOString(),
          trade: normalizeTrade(tradeKey ? row[tradeKey] : undefined),
          address: addressKey ? String(row[addressKey]).trim() || undefined : undefined,
          zipcode: zipKey ? String(row[zipKey]).trim() || undefined : undefined,
          valuation: valuationKey ? parseValuation(row[valuationKey]) : null,
          contractor: contractorKey ? String(row[contractorKey]).trim() || null : null,
          raw: row
        };

        permits.push(permit);

      } catch (error) {
        console.warn(`Failed to process row: ${error}`);
        continue; // Skip problematic rows
      }
    }

    console.log(`Processed ${permits.length} valid permits from ${rows.length} total rows`);
    return permits;

  } catch (error) {
    console.error(`Failed to fetch Houston weekly permits: ${error}`);
    throw error;
  }
}

/**
 * Export utility functions for testing
 */
export { findKey, normalizeTrade, parseValuation };


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

