from typing import Dict, Any, Iterable
import datetime as dt


class BaseAdapter:
    def __init__(self, cfg: Dict[str, Any], session=None):
        self.cfg = cfg
        self.session = session

    def fetch_since(
        self, since: dt.datetime, limit: int = 5000
    ) -> Iterable[Dict[str, Any]]:
        raise NotImplementedError
