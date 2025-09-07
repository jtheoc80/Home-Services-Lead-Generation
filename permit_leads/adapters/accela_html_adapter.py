from typing import Dict, Any, Iterable, Optional
import datetime as dt
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .base import BaseAdapter


class AccelaHTMLAdapter(BaseAdapter):
    """
    Very generic Accela/CitizenAccess results scraper.
    Assumes a public 'search results' page with a table of permits.
    This often needs per-site tuning for column headers/selectors and paging.

    Config:
      - type: accela_html
      - url: starting results/listing page
      - table_selector: e.g., "table#ctl00_PlaceHolderMain_dgvPermitList"
      - header_selector: "thead tr th" (optional; default)
      - row_selector: "tbody tr"
      - cell_selector: "td"
      - next_selector: "a[title='Next >']"  (optional; site-specific)
      - max_pages: 5
    """

    def __init__(self, cfg: Dict[str, Any], session=None):
        super().__init__(cfg, session)

    def _parse_table(self, soup: BeautifulSoup):
        table_sel = self.cfg.get("table_selector")
        row_sel = self.cfg.get("row_selector", "tbody tr")
        cell_sel = self.cfg.get("cell_selector", "td")
        header_sel = self.cfg.get("header_selector", "thead tr th")

        table = soup.select_one(table_sel) if table_sel else None
        if not table:
            return []

        headers = [th.get_text(strip=True) for th in table.select(header_sel)]
        rows = []
        for tr in table.select(row_sel):
            cells = [td.get_text(" ", strip=True) for td in tr.select(cell_sel)]
            if not cells:
                continue
            row = dict(zip(headers, cells))
            rows.append(row)
        return rows

    def fetch_since(
        self, since: dt.datetime, limit: int = 3000
    ) -> Iterable[Dict[str, Any]]:
        url = self.cfg["url"]
        next_sel = self.cfg.get("next_selector")
        max_pages = int(self.cfg.get("max_pages", 5))

        results = 0
        pages = 0
        while url and pages < max_pages and results < limit:
            resp = self.session.get(url)
            soup = BeautifulSoup(resp.text, "html.parser")
            for row in self._parse_table(soup):
                yield row
                results += 1
                if results >= limit:
                    break
            pages += 1
            if next_sel and results < limit:
                nxt = soup.select_one(next_sel)
                url = urljoin(url, nxt["href"]) if (nxt and nxt.get("href")) else None
            else:
                url = None

    # SourceAdapter interface methods
    def fetch(self, since_days: int) -> Iterable[bytes | str]:
        """Fetch raw HTML pages from Accela system."""
        url = self.cfg["url"]
        next_sel = self.cfg.get("next_selector")
        max_pages = int(self.cfg.get("max_pages", 5))

        pages = 0
        while url and pages < max_pages:
            resp = self.session.get(url)
            yield resp.text

            pages += 1
            if next_sel:
                soup = BeautifulSoup(resp.text, "html.parser")
                nxt = soup.select_one(next_sel)
                url = urljoin(url, nxt["href"]) if (nxt and nxt.get("href")) else None
            else:
                url = None

    def parse(self, raw: bytes | str) -> Iterable[Dict[str, Any]]:
        """Parse HTML page into records."""
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")

        soup = BeautifulSoup(raw, "html.parser")

        for row in self._parse_table(soup):
            yield row

    def normalize(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Accela record to standard format."""
        mappings = self.cfg.get("mappings", {})

        # Apply field mappings if configured
        normalized = {}
        for target_field, source_field in mappings.items():
            if source_field in row:
                normalized[target_field] = row[source_field]

        # Add standard fields with fallbacks for common Accela formats
        normalized.update(
            {
                "source": self.name,
                "permit_number": normalized.get("permit_number")
                or row.get("Permit Number")
                or row.get("Record Number")
                or "",
                "issued_date": normalized.get("issued_date")
                or row.get("Issued Date")
                or row.get("Issue Date")
                or "",
                "address": normalized.get("address")
                or row.get("Address")
                or row.get("Project Address")
                or "",
                "description": normalized.get("description")
                or row.get("Description")
                or row.get("Work Description")
                or "",
                "status": normalized.get("status") or row.get("Status") or "",
                "work_class": normalized.get("work_class")
                or row.get("Permit Type")
                or row.get("Record Type")
                or "",
                "category": normalized.get("category")
                or row.get("Category")
                or row.get("Permit Type")
                or "",
                "applicant": normalized.get("applicant")
                or row.get("Applicant")
                or row.get("Primary Contact")
                or "",
                "value": self._parse_value(
                    normalized.get("value") or row.get("Valuation") or row.get("Value")
                ),
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
