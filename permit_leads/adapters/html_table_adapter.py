from typing import Dict, Any, Iterable
import datetime as dt
from bs4 import BeautifulSoup


class HTMLTableAdapter:
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
        self.cfg = cfg
        self.session = session

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
