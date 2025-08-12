from typing import Dict, Any, Iterable
import datetime as dt

class SocrataAdapter:
    """
    Generic Socrata Open Data adapter.
    Config example:
      - name: Chicago Permits
        type: socrata
        domain: data.cityofchicago.org
        dataset_id: ydr8-5enu
        date_field: issue_date          # ISO8601-ish, varies by dataset
        mappings:
          permit_number: "permit_"
          address: "street_number,street_direction,street_name,street_type"
          description: "work_description"
          applicant: "contractor_name"
          status: "status"
          value: "estimated_cost"
          latitude: "latitude"
          longitude: "longitude"
          work_class: "permit_type"
          category: "permit_type"      # if dataset uses Residential/Commercial etc.
    """
    def __init__(self, cfg: Dict[str, Any], session=None):
        self.cfg = cfg
        self.session = session

    def _build_select(self) -> str:
        # Pull all columns; normalization selects what it needs.
        return "*"

    def _address_from_fields(self, rec: Dict[str, Any], field: str) -> str:
        # supports comma-separated list of fields
        parts = [p.strip() for p in field.split(",")]
        vals = []
        for p in parts:
            v = rec.get(p)
            if v is None:
                continue
            vals.append(str(v).strip())
        return " ".join([s for s in vals if s])

    def fetch_since(self, since: dt.datetime, limit: int = 5000) -> Iterable[Dict[str, Any]]:
        domain = self.cfg["domain"]
        dataset_id = self.cfg["dataset_id"]
        date_field = self.cfg.get("date_field")
        url = f"https://{domain}/resource/{dataset_id}.json"

        # Socrata supports SoQL with $where and $limit/$offset
        where = None
        if date_field:
            # ISO 8601
            since_iso = since.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            where = f"{date_field} >= '{since_iso}'"

        params = {
            "$select": self._build_select(),
            "$limit": 1000,
        }
        if where:
            params["$where"] = where

        total = 0
        offset = 0
        while total < limit:
            params["$offset"] = offset
            resp = self.session.get(url, params=params)
            data = resp.json()
            if not data:
                break
            # Optionally reshape some fields like address composition
            mappings = self.cfg.get("mappings", {})
            if "address" in mappings and "," in str(mappings["address"]):
                for row in data:
                    row["__address_composed"] = self._address_from_fields(row, mappings["address"])
            for row in data:
                yield row
            batch = len(data)
            total += batch
            offset += batch
            if batch < params["$limit"]:
                break
