from typing import Dict, Any, Iterable
import datetime as dt
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class AccelaHTMLAdapter:
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
        self.cfg = cfg
        self.session = session

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

    def fetch_since(self, since: dt.datetime, limit: int = 3000) -> Iterable[Dict[str, Any]]:
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
