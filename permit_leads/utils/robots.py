from urllib import robotparser
import time
import requests

class PoliteSession:
    def __init__(self, user_agent="PermitLeadBot/1.0 (+contact@example.com)", min_delay=1.0):
        self.user_agent = user_agent
        self.min_delay = float(min_delay)
        self._last = 0.0
        self._robots = {}

        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self.user_agent, "Accept": "application/json, text/html;q=0.9"})

    def _sleep(self):
        dt = time.time() - self._last
        if dt < self.min_delay:
            time.sleep(self.min_delay - dt)
        self._last = time.time()

    def _allowed(self, url: str) -> bool:
        from urllib.parse import urlparse, urljoin
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robots:
            rp = robotparser.RobotFileParser()
            rp.set_url(urljoin(base, "/robots.txt"))
            try:
                rp.read()
            except Exception:
                # be conservative
                self._robots[base] = None
                return True
            self._robots[base] = rp
        rp = self._robots[base]
        if rp is None:
            return True
        return rp.can_fetch(self.user_agent, url)

    def get(self, url, **kwargs):
        if not self._allowed(url):
            raise RuntimeError(f"Blocked by robots.txt: {url}")
        self._sleep()
        resp = self._session.get(url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp
