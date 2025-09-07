from typing import Dict, Any, Iterable, Optional
import datetime as dt
from bs4 import BeautifulSoup
from .base import BaseAdapter


class HTMLTableAdapter(BaseAdapter):
    """
    Very simple adapter for a static HTML table page that lists permits.
    Config example:
      - name: ExampleTown Permits (HTML)
        type: html_table
        url: https://example.gov/permits/recent.html
        table_selector: "table#permits"   # CSS selector
        mappings:
          permit_number: "Permit #"
          address: "Address"
          description: "Description"
          applicant: "Applicant"
          status: "Status"
          value: "Value"
          issued_date: "Issued"
          category: "Category"
    """

    def __init__(self, cfg: Dict[str, Any], session=None):
        super().__init__(cfg, session)

    def fetch_since(
        self, since: dt.datetime, limit: int = 5000
    ) -> Iterable[Dict[str, Any]]:
        url = self.cfg["url"]
        table_sel = self.cfg["table_selector"]
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.select_one(table_sel)
        if not table:
            return []

        # Build header map
        headers = [th.get_text(strip=True) for th in table.select("thead th")]
        if not headers:
            # try first row
            thead = table.find("thead")
            if not thead:
                first_tr = table.find("tr")
                headers = [
                    td.get_text(strip=True) for td in first_tr.find_all(["td", "th"])
                ]
        rows = []
        for tr in table.select("tbody tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
            row = dict(zip(headers, cells))
            rows.append(row)

        # filter by issued_date if present
        date_field = self.cfg.get("date_field", "Issued")
        out = []
        for r in rows:
            out.append(r)
            if len(out) >= limit:
                break
        return out

    # SourceAdapter interface methods
    def fetch(self, since_days: int) -> Iterable[bytes | str]:
        """Fetch raw HTML page."""
        url = self.cfg["url"]
        resp = self.session.get(url)
        yield resp.text

    def parse(self, raw: bytes | str) -> Iterable[Dict[str, Any]]:
        """Parse HTML table into records."""
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")

        table_sel = self.cfg["table_selector"]
        soup = BeautifulSoup(raw, "html.parser")
        table = soup.select_one(table_sel)
        if not table:
            return

        # Build header map
        headers = [th.get_text(strip=True) for th in table.select("thead th")]
        if not headers:
            # try first row
            thead = table.find("thead")
            if not thead:
                first_tr = table.find("tr")
                headers = [
                    td.get_text(strip=True) for td in first_tr.find_all(["td", "th"])
                ]

        for tr in table.select("tbody tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
            row = dict(zip(headers, cells))
            yield row

    def normalize(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize HTML table record to standard format."""
        mappings = self.cfg.get("mappings", {})

        # Apply field mappings if configured
        normalized = {}
        for target_field, source_field in mappings.items():
            if source_field in row:
                normalized[target_field] = row[source_field]

        # Add standard fields with fallbacks
        normalized.update(
            {
                "source": self.name,
                "permit_number": normalized.get("permit_number")
                or row.get("Permit #")
                or row.get("Permit")
                or "",
                "issued_date": normalized.get("issued_date")
                or row.get("Issued")
                or row.get("Date")
                or "",
                "address": normalized.get("address") or row.get("Address") or "",
                "description": normalized.get("description")
                or row.get("Description")
                or "",
                "status": normalized.get("status") or row.get("Status") or "",
                "work_class": normalized.get("work_class") or row.get("Type") or "",
                "category": normalized.get("category") or row.get("Category") or "",
                "applicant": normalized.get("applicant") or row.get("Applicant") or "",
                "value": self._parse_value(normalized.get("value") or row.get("Value")),
                "raw_json": row,
            }
        )

        return normalized

    def _parse_value(self, value_str: Any) -> Optional[float]:
        """Parse permit value from string."""
        if value_str is None:
            return None

        try:
            # Handle various value formats
            if isinstance(value_str, (int, float)):
                return float(value_str)

            value_str = str(value_str).strip()
            if not value_str:
                return None

            # Remove common prefixes and characters
            value_str = value_str.replace("$", "").replace(",", "").replace(" ", "")

            if value_str.lower() in ["n/a", "na", "none", "null", ""]:
                return None

            return float(value_str)
        except (ValueError, TypeError):
            return None
