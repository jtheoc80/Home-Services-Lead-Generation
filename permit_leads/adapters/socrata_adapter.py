from typing import Dict, Any, Iterable
import datetime as dt
import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class SocrataAdapter:
    """
    Generic Socrata Open Data adapter with incremental pulls and rate limiting.

    Supports Dallas (e7gq-4sah) and Austin (3syk-w9eu) building permits APIs.

    Config example:
      - name: Dallas Building Permits
        type: socrata
        domain: www.dallasopendata.com
        dataset_id: e7gq-4sah
        updated_field: issued_date      # Field for incremental updates
        primary_key: permit_number      # Unique identifier field
        date_field: issued_date          # ISO8601-ish, varies by dataset
        mappings:
          permit_number: "permit_number"
          address: "street_number,street_direction,street_name,street_type"
          description: "work_description"
          applicant: "contractor_name"
          status: "permit_status"
          value: "estimated_cost"
          latitude: "latitude"
          longitude: "longitude"
          work_class: "permit_type_desc"
          category: "permit_class"
    """

    # Rate limiting: maximum 5 requests per second for Socrata APIs
    MAX_REQUESTS_PER_SECOND = 5
    MIN_REQUEST_INTERVAL = 1.0 / MAX_REQUESTS_PER_SECOND  # 0.2 seconds

    def __init__(self, cfg: Dict[str, Any], session=None):
        self.cfg = cfg
        self.session = session or self._create_session()
        self._last_request_time = 0

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy for Socrata APIs."""
        session = requests.Session()

        # Retry strategy for Socrata APIs
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set headers for Socrata APIs
        session.headers.update(
            {
                "User-Agent": "PermitLeadBot/1.0 (Texas Building Permits)",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            }
        )

        return session

    def _rate_limit(self):
        """Enforce rate limiting for Socrata APIs."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            sleep_time = self.MIN_REQUEST_INTERVAL - elapsed
            logger.debug(
                f"Rate limiting Socrata API: sleeping for {sleep_time:.3f} seconds"
            )
            time.sleep(sleep_time)
        self._last_request_time = time.time()

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

    def fetch_since(
        self, since: dt.datetime, limit: int = 5000
    ) -> Iterable[Dict[str, Any]]:
        """
        Fetch records with incremental updates and rate limiting.

        Args:
            since: Only return records updated since this timestamp
            limit: Maximum number of records to return
        """
        domain = self.cfg["domain"]
        dataset_id = self.cfg["dataset_id"]
        updated_field = self.cfg.get("updated_field")
        date_field = self.cfg.get("date_field")
        primary_key = self.cfg.get("primary_key")

        url = f"https://{domain}/resource/{dataset_id}.json"

        # Build SoQL where clause for incremental updates
        where_clauses = []

        if updated_field and since:
            # Use updated_field for incremental pulls
            since_iso = since.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            where_clauses.append(f"{updated_field} >= '{since_iso}'")
        elif date_field and since:
            # Fallback to date_field if no updated_field
            since_iso = since.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            where_clauses.append(f"{date_field} >= '{since_iso}'")

        # Build SoQL parameters
        params = {
            "$select": self._build_select(),
            "$limit": 1000,  # Socrata recommended batch size
            "$order": (
                f"{updated_field or date_field} DESC"
                if (updated_field or date_field)
                else primary_key
            ),
        }

        if where_clauses:
            params["$where"] = " AND ".join(where_clauses)

        logger.info(f"Fetching from Socrata: {domain}/{dataset_id}")
        logger.debug(f"Query params: {params}")

        total_fetched = 0
        offset = 0

        while total_fetched < limit:
            # Apply rate limiting
            self._rate_limit()

            # Set pagination
            params["$offset"] = offset
            current_limit = min(1000, limit - total_fetched)
            params["$limit"] = current_limit

            try:
                logger.debug(f"Fetching batch: offset={offset}, limit={current_limit}")
                resp = self.session.get(url, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                if not data:
                    logger.info("No more data available from Socrata API")
                    break

                # Process field mappings for address composition
                mappings = self.cfg.get("mappings", {})
                if "address" in mappings and "," in str(mappings["address"]):
                    for row in data:
                        row["__address_composed"] = self._address_from_fields(
                            row, mappings["address"]
                        )

                # Add source metadata
                for row in data:
                    row["_source_api"] = f"{domain}/{dataset_id}"
                    row["_fetched_at"] = dt.datetime.now().isoformat()
                    yield row

                batch_size = len(data)
                total_fetched += batch_size
                offset += batch_size

                logger.info(f"Fetched {batch_size} records, total: {total_fetched}")

                # If we got fewer records than requested, we've reached the end
                if batch_size < current_limit:
                    logger.info("Reached end of Socrata dataset")
                    break

            except requests.RequestException as e:
                logger.error(f"Error fetching from Socrata API: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error processing Socrata data: {e}")
                break

        logger.info(f"Completed Socrata fetch: {total_fetched} total records")

    def get_record_count(self, since: dt.datetime = None) -> int:
        """Get total count of records available."""
        domain = self.cfg["domain"]
        dataset_id = self.cfg["dataset_id"]
        updated_field = self.cfg.get("updated_field")

        url = f"https://{domain}/resource/{dataset_id}.json"

        where_clause = None
        if updated_field and since:
            since_iso = since.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            where_clause = f"{updated_field} >= '{since_iso}'"

        params = {"$select": "COUNT(*) as count"}

        if where_clause:
            params["$where"] = where_clause

        try:
            self._rate_limit()
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if data and len(data) > 0:
                return int(data[0].get("count", 0))

        except Exception as e:
            logger.warning(f"Could not get record count from Socrata: {e}")

        return 0
