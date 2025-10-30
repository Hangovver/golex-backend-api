
from collections import defaultdict
import threading, json, time

class PrefsStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._data = defaultdict(dict)  # anonId -> dict

    def get(self, anon_id: str) -> dict:
        with self._lock:
            return self._data.get(anon_id, {}) or {}

    def set(self, anon_id: str, data: dict) -> dict:
        with self._lock:
            cur = self._data.get(anon_id) or {}
            cur.update(data or {})
            # normalize sets as unique lists
            for k in ("favLeagues","favTeams","favFixtures"):
                if k in cur and isinstance(cur[k], list):
                    cur[k] = list(dict.fromkeys([str(x) for x in cur[k]]))
            self._data[anon_id] = cur
            return cur

STORE = PrefsStore()
