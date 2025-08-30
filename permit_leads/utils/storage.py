from pathlib import Path
import sqlite3
import csv
from typing import Dict, Any, List

SCHEMA = """
CREATE TABLE IF NOT EXISTS permits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    permit_number TEXT,
    issued_date TEXT,
    status TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zipcode TEXT,
    applicant TEXT,
    contractor TEXT,
    description TEXT,
    value REAL,
    work_class TEXT,
    category TEXT,
    latitude REAL,
    longitude REAL,
    raw JSON,
    UNIQUE(source, permit_number)
);
"""


class Storage:
    def __init__(self, db_path: Path, csv_path: Path):
        self.db_path = Path(db_path)
        self.csv_path = Path(csv_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute(SCHEMA)
        self.conn.commit()
        self._ensure_csv_header()

    def _ensure_csv_header(self):
        if not self.csv_path.exists():
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(
                    [
                        "source",
                        "permit_number",
                        "issued_date",
                        "status",
                        "address",
                        "city",
                        "state",
                        "zipcode",
                        "applicant",
                        "contractor",
                        "description",
                        "value",
                        "work_class",
                        "category",
                        "latitude",
                        "longitude",
                    ]
                )

    def save(self, rec: Dict[str, Any]) -> bool:
        # insert into sqlite
        try:
            self.conn.execute(
                """INSERT OR IGNORE INTO permits
                (source, permit_number, issued_date, status, address, city, state, zipcode, applicant, contractor, description, value, work_class, category, latitude, longitude, raw)
                VALUES (:source, :permit_number, :issued_date, :status, :address, :city, :state, :zipcode, :applicant, :contractor, :description, :value, :work_class, :category, :latitude, :longitude, :raw)""",
                {**rec, "raw": rec.get("raw_json", "{}")},
            )
            self.conn.commit()
        except sqlite3.Error:
            return False

        # append to CSV (best-effort)
        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(
                    [
                        rec.get(k, "")
                        for k in [
                            "source",
                            "permit_number",
                            "issued_date",
                            "status",
                            "address",
                            "city",
                            "state",
                            "zipcode",
                            "applicant",
                            "contractor",
                            "description",
                            "value",
                            "work_class",
                            "category",
                            "latitude",
                            "longitude",
                        ]
                    ]
                )
        except Exception:
            pass
        return True

    def latest(self, n: int = 10) -> List[dict]:
        cur = self.conn.execute(
            """SELECT source, permit_number, issued_date, address, applicant, contractor, description, value, status
                                   FROM permits ORDER BY issued_date DESC, id DESC LIMIT ?""",
            (n,),
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
