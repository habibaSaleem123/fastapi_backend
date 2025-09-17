import time
import threading
import re
from collections import defaultdict
from fastapi import HTTPException, Request, status

class MemoryRateLimiter:
    """
    Very simple in-memory rate limiter for a single-process dev server.

    Limit formats:
      - "N/SECONDS" (e.g., "30/60")
      - "N/s", "N/sec"
      - "N/m", "N/min"
      - "N/h", "N/hr", "N/hour"
      - "N/d", "N/day"
      - "N/5m", "N/10s", etc.
    """
    def __init__(self):
        self._buckets = defaultdict(list)  # key -> [timestamps]
        self._lock = threading.Lock()

    @staticmethod
    def _unit_to_seconds(unit: str) -> int:
        unit = unit.lower()
        if unit in ("s", "sec", "secs", "second", "seconds"):
            return 1
        if unit in ("m", "min", "mins", "minute", "minutes"):
            return 60
        if unit in ("h", "hr", "hrs", "hour", "hours"):
            return 3600
        if unit in ("d", "day", "days"):
            return 86400
        if unit.isdigit():
            return int(unit)
        raise ValueError(f"Unknown time unit: {unit}")

    def parse_limit(self, limit_str: str) -> tuple[int, int]:
        try:
            count_part, window_part = limit_str.split("/", 1)
            count = int(count_part.strip())

            m = re.fullmatch(r"\s*(\d+)?\s*([a-zA-Z]+)?\s*", window_part)
            if not m:
                window = int(window_part)
                return count, window

            num, unit = m.groups()
            if unit:
                if num is None:
                    window = self._unit_to_seconds(unit)
                else:
                    window = int(num) * self._unit_to_seconds(unit)
            else:
                window = int(num)

            return count, window
        except Exception:
            raise ValueError(
                "Invalid rate limit format. Expected 'count/seconds' or units like '30/min', '100/5m'."
            )

    def hit(self, key: str, limit_str: str):
        count, window = self.parse_limit(limit_str)
        now = time.time()
        with self._lock:
            q = self._buckets[key]
            while q and (now - q[0]) > window:
                q.pop(0)
            if len(q) >= count:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
            q.append(now)

limiter = MemoryRateLimiter()

def rate_limit(limit_str: str, scope: str):
    """
    Use in routes like:
      @router.get(..., dependencies=[Depends(rate_limit("30/min", "google_start"))])
    Returns a callable dependency (NOT a Depends).
    """
    def dep(req: Request):
        ip = getattr(req.client, "host", "unknown")
        key = f"{ip}:{scope}"
        limiter.hit(key, limit_str)
    return dep
