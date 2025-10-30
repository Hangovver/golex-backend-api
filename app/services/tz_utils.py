
from typing import Optional
from datetime import datetime
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None

def to_local_time(dt_str: str, tz: str = "Europe/Istanbul") -> Optional[str]:
    if not dt_str:
        return None
    try:
        # parse ISO8601 (e.g., 2024-10-26T19:00:00Z or with offset)
        # Remove Z if present for fromisoformat compatibility
        s = dt_str.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if ZoneInfo is None:
            # if tz not available, return original string
            return dt_str
        local = dt.astimezone(ZoneInfo(tz))
        return local.isoformat()
    except Exception:
        return None
