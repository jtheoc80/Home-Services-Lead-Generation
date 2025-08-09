from typing import Dict, Any, Iterable
import datetime as dt
from urllib.parse import urlencode
import math

class ArcGISFeatureServiceAdapter:
    """
    Query an ArcGIS FeatureServer/MapServer layer for permits.
    Works with endpoints like:
      https://<host>/arcgis/rest/services/<path>/<FeatureServer|MapServer>/<layer>/query

    Required config:
      - name: Display name
      - type: arcgis_feature_service
      - url:  full /query endpoint OR layer endpoint (we'll append /query)
      - date_field: Field to filter by date (e.g., 'GAL_REC_DATE', 'ISSUEDDATE')
      - mappings: dict for field mapping into normalized record (optional)

    Notes:
      - We page using resultOffset/resultRecordCount up to 'limit' rows.
      - Returns raw ArcGIS attributes; normalization handled upstream.
    """
    def __init__(self, cfg: Dict[str, Any], session=None):
        self.cfg = cfg
        self.session = session

    def _query_url(self) -> str:
        url = self.cfg["url"]
        return url if url.rstrip('/').endswith('/query') else url.rstrip('/') + '/query'

    def fetch_since(self, since: dt.datetime, limit: int = 10000) -> Iterable[Dict[str, Any]]:
        date_field = self.cfg["date_field"]
        url = self._query_url()
        where = f"{date_field} >= TIMESTAMP '{since.strftime('%Y-%m-%d %H:%M:%S')}'"

        page_size = 2000
        out_fields = self.cfg.get("out_fields", "*")

        fetched = 0
        offset = 0
        while fetched < limit:
            params = {
                "where": where,
                "outFields": out_fields,
                "f": "json",
                "returnGeometry": "false",
                "resultOffset": offset,
                "resultRecordCount": page_size,
                "orderByFields": f"{date_field} DESC"
            }
            resp = self.session.get(url, params=params)
            data = resp.json()
            feats = data.get("features", [])
            if not feats:
                break
            for feat in feats:
                attrs = feat.get("attributes", {})
                yield attrs
                fetched += 1
                if fetched >= limit:
                    break
            if len(feats) < page_size:
                break
            offset += len(feats)
