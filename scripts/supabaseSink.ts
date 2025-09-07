export type Permit = {
  source_system: "city_of_houston";
  permit_id: string;
  issue_date: string;  // ISO
  trade: string;
  address?: string;
  zipcode?: string;
  valuation?: number | null;
  contractor?: string | null;
};