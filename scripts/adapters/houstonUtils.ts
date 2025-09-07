/**
 * Utility functions for Houston permit data processing
 */

/**
 * Normalize trade type from raw permit data
 */
export function normTrade(v: string | undefined): string {
  const s = (v || "").toLowerCase();
  if (s.includes("elect")) return "Electrical";
  if (s.includes("plumb")) return "Plumbing";
  if (s.includes("mech")) return "Mechanical";
  return "General";
}